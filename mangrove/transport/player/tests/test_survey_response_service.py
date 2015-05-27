from collections import OrderedDict
from unittest import TestCase
from mock import Mock, patch, PropertyMock, MagicMock
from mangrove.datastore.entity_type import define_type
from mangrove.feeds.enriched_survey_response import EnrichedSurveyResponseBuilder
from mangrove.form_model.validation import NumericRangeConstraint
from mangrove.form_model.field import TextField, IntegerField, UniqueIdField
from mangrove.datastore.documents import EntityDocument
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import DataRecord, Entity, get_by_short_code_include_voided
from mangrove.datastore.tests.test_data import TestData
from mangrove.errors.MangroveException import MangroveException, FormModelDoesNotExistsException
from mangrove.form_model.form_model import FormModel, MOBILE_NUMBER_FIELD, NAME_FIELD
from mangrove.transport.contract.request import Request
from mangrove.transport.contract.transport_info import TransportInfo
from mangrove.transport.player.tests.test_reporter import TestReporter
from mangrove.transport.repository.reporters import REPORTER_ENTITY_TYPE
from mangrove.transport.services.survey_response_service import SurveyResponseService
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.transport.repository.survey_responses import SurveyResponse


def assert_submission_log_is(form_code):
    def _assert(self, other):
        return other.form_code == form_code

    return _assert


class TestSurveyResponseService(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.survey_response_service = SurveyResponseService(self.dbm)

    def form_model(self):
        question1 = UniqueIdField(unique_id_type='clinic',name="entity_question", code="q1", label="What is associated entity",
                              )
        question2 = IntegerField(name="question1_Name", code="q2", label="What is your name",
                                 constraints=[NumericRangeConstraint(min=10, max=100)])
        return FormModel(self.dbm, name="aids", label="Aids form_model",
                         form_code="aids", fields=[question1, question2])

    #TODO : Need to add validations for incompatible data types -> eg. string for number. This validation is hadled outside the service for now.
    def test_edit_survey_response_when_fields_constraints_are_not_satisfied(self):
        survey_response = Mock(spec=SurveyResponse)
        with patch('mangrove.transport.services.survey_response_service.by_short_code') as get_reporter:
            with patch('mangrove.datastore.entity.by_short_code') as get_entity:
                with patch(
                        'mangrove.transport.services.survey_response_service.get_form_model_by_code') as get_form_model:
                    get_reporter.return_value = Mock(spec=Entity)
                    get_entity.return_value = Mock(spec=Entity)
                    get_form_model.return_value = self.form_model()
                    transport_info = TransportInfo('web', 'src', 'dest')
                    values = {'form_code': 'aids', 'q1': 'a1', 'q2': '200'}

                    request = Request(values, transport_info)
                    response = self.survey_response_service.edit_survey('aids', values, [], survey_response)
                    self.assertFalse(response.success)
                    self.assertEquals('aids', response.form_code)
                    self.assertEquals(OrderedDict([('q2', u'Answer 200 for question q2 is greater than allowed.')]),
                                      response.errors)
                    self.assertEquals(['clinic'], response.entity_type)
                    self.assertEquals(OrderedDict([('q1', 'a1')]), response.processed_data)
                    self.assertIsNotNone(response.survey_response_id)

                    assert not survey_response.update.called

    def test_survey_response_event_created_when_survey_response_created(self):
        manager = Mock(spec=DatabaseManager)
        feed_manager = Mock(spec=DatabaseManager)
        survey_response_service = SurveyResponseService(manager, feeds_dbm=feed_manager)

        values = {'ID': 'short_code', 'Q1': 'name', 'Q2': '80', 'Q3': 'a'}
        transport_info = TransportInfo('web', 'src', 'dest')
        request = Request(values, transport_info)

        additional_dictionary = {'project': {'name': 'someproject', 'status': 'active', 'id': 'someid'}}
        with patch('mangrove.transport.services.survey_response_service.by_short_code') as get_reporter:
            with patch(
                    'mangrove.transport.services.survey_response_service.get_form_model_by_code') as get_form_model_by_code:
                with patch('mangrove.datastore.entity.by_short_code') as by_short_code:
                    with patch(
                            'mangrove.transport.services.survey_response_service.EnrichedSurveyResponseBuilder')as builder:
                        with patch("mangrove.form_model.form_submission.DataRecordDocument") as DataRecordDocumentMock:
                            get_reporter.return_value = Mock(spec=Entity)
                            builder.return_value = Mock(spec=EnrichedSurveyResponseBuilder)
                            entity_mock = MagicMock(spec=Entity)
                            entity_mock._doc = EntityDocument()
                            by_short_code.return_value = entity_mock
                            mock_form_model = MagicMock(spec=FormModel)
                            mock_form_model._dbm = manager
                            mock_form_model._doc = MagicMock()
                            mock_form_model._data = {}
                            mock_form_model.validate_submission.return_value = OrderedDict(values), OrderedDict('')
                            mock_form_model.is_entity_registration_form.return_value = False
                            mock_form_model.entity_questions = []
                            mock_form_model.entity_type = 'sometype'
                            get_form_model_by_code.return_value = mock_form_model
                            survey_response_service.save_survey('CL1', values, [], transport_info,'',
                                                                additional_dictionary)
                            self.assertEquals(1, feed_manager._save_document.call_count)


    def test_feeds_created_if_subject_not_found_for_a_submission(self):
        manager = Mock(spec=DatabaseManager)
        feed_manager = Mock(spec=DatabaseManager)
        values = {'ID': 'short_code', 'Q1': 'name', 'Q2': '80', 'Q3': 'a'}
        transport_info = TransportInfo('web', 'src', 'dest')
        request = Request(values, transport_info)

        additional_dictionary = {'project': {'name': 'someproject', 'status': 'active', 'id': 'someid'}}

        survey_response_service = SurveyResponseService(manager, feeds_dbm=feed_manager)

        with patch('mangrove.transport.services.survey_response_service.by_short_code') as get_reporter:
            with patch(
                    'mangrove.transport.services.survey_response_service.get_form_model_by_code') as get_form_model_by_code:
                with patch('mangrove.datastore.entity.by_short_code') as by_short_code:
                    with patch(
                            'mangrove.transport.services.survey_response_service.DataFormSubmission') as data_form_submission:
                        with patch(
                                'mangrove.transport.services.survey_response_service.EnrichedSurveyResponseBuilder')as builder:
                            get_reporter.return_value = Mock(spec=Entity)
                            builder.return_value = Mock(spec=EnrichedSurveyResponseBuilder)
                            instance_mock = data_form_submission.return_value
                            type(instance_mock).is_valid = PropertyMock(return_value=True)
                            type(instance_mock).data_record_id = PropertyMock(return_value='sdsddsd')
                            instance_mock.save.side_effect = MangroveException("subject not found")

                            by_short_code.return_value = Mock(spec=Entity)
                            mock_form_model = MagicMock(spec=FormModel)
                            mock_form_model._dbm = manager
                            mock_form_model._doc = MagicMock()
                            mock_form_model._data = {}
                            mock_form_model.validate_submission.return_value = values, ""
                            get_form_model_by_code.return_value = mock_form_model

                            try:
                                survey_response_service.save_survey('CL1', values, [], transport_info, '',
                                                                    additional_dictionary)
                                self.fail('the subject not found exception should be propagated')
                            except MangroveException:
                                feed_manager._save_document.assert_called_once()


    def test_response_has_no_error_when_feed_creation_fails(self):
        manager = Mock(spec=DatabaseManager)
        feed_manager = Mock(spec=DatabaseManager)
        values = {'ID': 'short_code', 'Q1': 'name', 'Q2': '80', 'Q3': 'a'}
        transport_info = TransportInfo('web', 'src', 'dest')
        request = Request(values, transport_info)

        additional_dictionary = {'project': {'name': 'someproject', 'status': 'active', 'id': 'someid'}}

        survey_response_service = SurveyResponseService(manager, feeds_dbm=feed_manager)

        with patch('mangrove.transport.services.survey_response_service.by_short_code') as get_reporter:
            with patch(
                    'mangrove.transport.services.survey_response_service.get_form_model_by_code') as get_form_model_by_code:
                with patch('mangrove.datastore.entity.by_short_code') as by_short_code:
                    with patch(
                            'mangrove.transport.services.survey_response_service.DataFormSubmission') as data_form_submission:
                        with patch(
                                'mangrove.transport.services.survey_response_service.EnrichedSurveyResponseBuilder')as builder:
                            get_reporter.return_value = Mock(spec=Entity)
                            builder.feed_document.side_effect = Exception('Some error')
                            builder.return_value = builder
                            instance_mock = data_form_submission.return_value
                            type(instance_mock).is_valid = PropertyMock(return_value=True)
                            type(instance_mock).data_record_id = PropertyMock(return_value='sdsddsd')
                            type(instance_mock).errors = PropertyMock(return_value='')

                            by_short_code.return_value = Mock(spec=Entity)
                            mock_form_model = MagicMock(spec=FormModel)
                            mock_form_model._dbm = manager
                            mock_form_model._doc = MagicMock()
                            mock_form_model._data = {}
                            mock_form_model.validate_submission.return_value = values, ""
                            get_form_model_by_code.return_value = mock_form_model
                            response = survey_response_service.save_survey('CL1', values, [], transport_info, '',
                                                                           additional_dictionary)
                            self.assertFalse(response.errors)
                            self.assertTrue(response.feed_error_message)


class TestSurveyResponseServiceIT(MangroveTestCase):
    def setUp(self):
        super(TestSurveyResponseServiceIT, self).setUp()
        register_datasender(self.manager)

    def tearDown(self):
        super(TestSurveyResponseServiceIT, self).tearDown()

    def test_survey_response_is_saved(self):
        test_data = TestData(self.manager)
        survey_response_service = SurveyResponseService(self.manager)

        values = {'ID': test_data.entity1.short_code, 'Q1': 'name', 'Q2': '80', 'Q3': 'a'}
        transport_info = TransportInfo('web', 'src', 'dest')
        request = Request(values, transport_info)
        response = survey_response_service.save_survey('CL1', values, [], transport_info, 'rep2')

        self.assertTrue(response.success)
        self.assertEqual(0, response.errors.__len__())
        self.assertIsNotNone(response.datarecord_id)
        self.assertIsNotNone(response.survey_response_id)
        self.assertEqual(test_data.entity_type, response.entity_type)
        self.assertEqual('CL1', response.form_code)
        self.assertEqual('1', response.short_code)
        self.assertDictEqual(OrderedDict([('Q1', 'name'), ('Q3', ['RED']), ('Q2', 80), ('ID', u'1')]),
                             response.processed_data)

        survey_response = SurveyResponse.get(self.manager, response.survey_response_id)
        self.assertDictEqual({'Q1': 'name', 'Q3': 'a', 'Q2': '80', 'ID': '1'}, survey_response.values)
        self.assertDictEqual({'Q1': 'name', 'Q3': 'a', 'Q2': '80', 'ID': '1'}, survey_response.values)
        self.assertEqual(test_data.form_model.revision, survey_response.form_model_revision)
        self.assertEqual(True, survey_response.status)
        self.assertIsNotNone(survey_response.data_record)

    def test_survey_response_is_saved_with_reporter_id_in_upper_case(self):
        test_data = TestData(self.manager)
        survey_response_service = SurveyResponseService(self.manager)

        values = {'ID': test_data.entity1.short_code, 'Q1': 'name', 'Q2': '80', 'Q3': 'a'}
        transport_info = TransportInfo('web', 'src', 'dest')
        request = Request(values, transport_info)
        response = survey_response_service.save_survey('CL1', values, [], transport_info, 'REP2')

        self.assertTrue(response.success)
        self.assertEqual(0, response.errors.__len__())
        self.assertIsNotNone(response.datarecord_id)
        self.assertIsNotNone(response.survey_response_id)
        self.assertEqual(test_data.entity_type, response.entity_type)
        self.assertEqual('CL1', response.form_code)
        self.assertEqual('1', response.short_code)
        self.assertDictEqual(OrderedDict([('Q1', 'name'), ('Q3', ['RED']), ('Q2', 80), ('ID', u'1')]),
                             response.processed_data)

        survey_response = SurveyResponse.get(self.manager, response.survey_response_id)
        self.assertDictEqual({'Q1': 'name', 'Q3': 'a', 'Q2': '80', 'ID': '1'}, survey_response.values)
        self.assertDictEqual({'Q1': 'name', 'Q3': 'a', 'Q2': '80', 'ID': '1'}, survey_response.values)
        self.assertEqual(test_data.form_model.revision, survey_response.form_model_revision)
        self.assertEqual(True, survey_response.status)
        self.assertIsNotNone(survey_response.data_record)

    def test_exception_is_raised_for_invalid_short_code_submissions(self):
        survey_response_service = SurveyResponseService(self.manager)
        with patch('mangrove.transport.services.survey_response_service.get_active_form_model') as mock_get_active_form_model:
            mock_get_active_form_model.side_effect = FormModelDoesNotExistsException("form_code")
            values = {'ID': "invalid", 'Q1': 'name', 'Q2': '80', 'Q3': 'a'}
            transport_info = TransportInfo('web', 'src', 'dest')
            request = Request(values, transport_info)
            self.assertRaises(MangroveException, survey_response_service.save_survey, 'CL1', values, [], transport_info, '')

    def test_survey_response_is_edited_and_new_submission_and_datarecord_is_created(self):
        test_data = TestData(self.manager)
        survey_response_service = SurveyResponseService(self.manager)

        values = {'ID': test_data.entity1.short_code, 'Q1': 'name', 'Q2': '80', 'Q3': 'a'}
        transport_info = TransportInfo('web', 'src', 'dest')
        request = Request(values, transport_info)

        saved_response = survey_response_service.save_survey('CL1', values, [], transport_info, "rep2")
        self.assertDictEqual(OrderedDict([('Q1', 'name'), ('Q3', ['RED']), ('Q2', 80), ('ID', u'1')]),
                             saved_response.processed_data)

        new_values = {'ID': test_data.entity1.short_code, 'Q1': 'new_name', 'Q2': '430', 'Q3': 'b'}
        survey_response_to_edit = SurveyResponse.get(self.manager, saved_response.survey_response_id)
        edited_response = survey_response_service.edit_survey('CL1', new_values, [],
                                                              survey_response_to_edit)

        self.assertTrue(edited_response.success)
        self.assertEqual(0, edited_response.errors.__len__())
        self.assertIsNotNone(edited_response.datarecord_id)
        self.assertIsNotNone(edited_response.survey_response_id)
        self.assertEqual(test_data.entity_type, edited_response.entity_type)
        self.assertEqual('CL1', edited_response.form_code)
        self.assertDictEqual(OrderedDict([('Q1', 'new_name'), ('Q3', ['YELLOW']), ('Q2', 430), ('ID', u'1')]),
                             edited_response.processed_data)

        self.assertNotEquals(saved_response.datarecord_id, edited_response.datarecord_id)

        old_data_record = DataRecord.get(self.manager, saved_response.datarecord_id)
        self.assertTrue(old_data_record.voided)
        new_data_record = DataRecord.get(self.manager, edited_response.datarecord_id)
        self.assertFalse(new_data_record.voided)

        edited_survey_response = SurveyResponse.get(self.manager, edited_response.survey_response_id)
        self.assertEquals(1, len(edited_survey_response._doc.data_record_history))
        self.assertEquals(old_data_record.id, edited_survey_response._doc.data_record_history[0])


def register_datasender(dbm):
    define_type(dbm, ["reporter"])
    TestReporter.register(dbm,
                          data=[(MOBILE_NUMBER_FIELD, "1234567890"),
                                (NAME_FIELD, "B")],
                          location=None,
                          source="sms",
                          short_code="rep2")

    return get_by_short_code_include_voided(dbm, "rep2", REPORTER_ENTITY_TYPE).id
