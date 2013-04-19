from collections import OrderedDict
from unittest import TestCase
from mock import Mock, patch, call
from mangrove.form_model.validation import NumericRangeConstraint
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.field import TextField, IntegerField
from mangrove.datastore.documents import SurveyResponseDocument
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.datastore.entity import DataRecord, Entity
from mangrove.datastore.tests.test_data import TestData
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, InactiveFormModelException
from mangrove.form_model.form_model import FormModel
from mangrove.transport.contract.request import Request
from mangrove.transport.contract.transport_info import TransportInfo
from mangrove.transport.services.survey_response_service import SurveyResponseService
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.transport.contract.submission import Submission
from mangrove.transport.repository.survey_responses import SurveyResponse

def assert_submission_log_is(form_code):
    def _assert(self, other):
        return other.form_code == form_code

    return _assert


def assert_survey_response_doc_is(form_code):
    def _assert(self, other):
        return other.form_code == form_code

    return _assert


class TestSurveyResponseService(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.survey_response_service = SurveyResponseService(self.dbm)

    def test_save_survey_response_should_create_submission_when_form_is_invalid(self):
        SubmissionLogDocument.__eq__ = assert_submission_log_is('nonexistant_form_code')

        with patch.object(self.dbm, '_save_document') as save_document:
            with patch('mangrove.transport.services.survey_response_service.get_form_model_by_code') as get_form_model:
                get_form_model.side_effect = FormModelDoesNotExistsException('nonexistant_form_code')
                transport_info = TransportInfo('web', 'src', 'dest')
                values = {'form_code': 'nonexistant_form_code', 'q1': 'a1', 'q2': 'a2'}

                request = Request(values, transport_info)
                self.assertRaises(FormModelDoesNotExistsException, self.survey_response_service.save_survey,
                    'nonexistant_form_code', values, [], transport_info,
                    request.message)
                get_form_model.assert_has_calls([call(self.dbm, 'nonexistant_form_code')])
                save_document.assert_has_calls([call(SubmissionLogDocument())])

    def test_save_survey_response_should_create_submission_when_form_is_inactive(self):
        SubmissionLogDocument.__eq__ = assert_submission_log_is('nonexistant_form_code')
        SurveyResponseDocument.__eq__ = assert_survey_response_doc_is('nonexistant_form_code')

        form_model = Mock(spec=FormModel)
        with patch('mangrove.transport.services.survey_response_service.get_form_model_by_code') as patched_form_model:
            patched_form_model.return_value = form_model
            form_model.is_inactive.return_value = True
            self.dbm._save_document.return_value = SubmissionLogDocument()

            values = {'form_code': 'some_form_code', 'q1': 'a1', 'q2': 'a2'}
            transport_info = TransportInfo('web', 'src', 'dest')
            request = Request(values, transport_info)
            self.assertRaises(InactiveFormModelException, self.survey_response_service.save_survey, 'some_form_code',
                values, [], transport_info, request.message)
            calls = [call(self.dbm, 'some_form_code')]
            patched_form_model.assert_has_calls(calls)

    def test_save_survey_response_should_create_submission_when_form_code_is_invalid(self):
        SubmissionLogDocument.__eq__ = assert_submission_log_is('nonexistant_form_code')
        SurveyResponseDocument.__eq__ = assert_survey_response_doc_is('nonexistant_form_code')

        with patch.object(self.dbm, '_save_document') as save_document:
            with patch('mangrove.transport.services.survey_response_service.get_form_model_by_code') as get_form_model:
                get_form_model.side_effect = FormModelDoesNotExistsException('nonexistant_form_code')
                transport_info = TransportInfo('web', 'src', 'dest')
                values = {'form_code': 'nonexistant_form_code', 'q1': 'a1', 'q2': 'a2'}

                request = Request(values, transport_info)
                self.assertRaises(FormModelDoesNotExistsException, self.survey_response_service.save_survey,
                    'nonexistant_form_code', values, [], transport_info,
                    request.message)
                get_form_model.assert_has_calls([call(self.dbm, 'nonexistant_form_code')])
                save_document.assert_has_calls([call(SubmissionLogDocument())])

    def test_edit_survey_response_should_create_submission_when_form_is_inactive(self):
        form_model = Mock(spec=FormModel)
        with patch('mangrove.transport.services.survey_response_service.get_form_model_by_code') as patched_form_model:
            patched_form_model.return_value = form_model
            form_model.is_inactive.return_value = True
            self.dbm._save_document.return_value = SubmissionLogDocument()

            values = {'form_code': 'some_form_code', 'q1': 'a1', 'q2': 'a2'}
            transport_info = TransportInfo('web', 'src', 'dest')
            request = Request(values, transport_info)
            self.assertRaises(InactiveFormModelException, self.survey_response_service.edit_survey, 'some_form_code',
                values, [], transport_info, request.message, None)
            calls = [call(self.dbm, 'some_form_code')]
            patched_form_model.assert_has_calls(calls)

    def test_save_survey_response_should_create_submission_when_form_code_is_invalid(self):
        SubmissionLogDocument.__eq__ = assert_submission_log_is('nonexistant_form_code')
        SurveyResponseDocument.__eq__ = assert_survey_response_doc_is('nonexistant_form_code')

        with patch.object(self.dbm, '_save_document') as save_document:
            with patch('mangrove.transport.services.survey_response_service.get_form_model_by_code') as get_form_model:
                get_form_model.side_effect = FormModelDoesNotExistsException('nonexistant_form_code')
                transport_info = TransportInfo('web', 'src', 'dest')
                values = {'form_code': 'nonexistant_form_code', 'q1': 'a1', 'q2': 'a2'}

                request = Request(values, transport_info)
                self.assertRaises(FormModelDoesNotExistsException, self.survey_response_service.save_survey,
                    'nonexistant_form_code', values, [], transport_info,
                    request.message)
                get_form_model.assert_has_calls([call(self.dbm, 'nonexistant_form_code')])
                save_document.assert_has_calls([call(SubmissionLogDocument())])

    def form_model(self):
        string_type = DataDictType(self.dbm, name='Default String Datadict Type', slug='string_default',
            primitive_type='string')
        integer_type = DataDictType(self.dbm, name='Default String Integer Type', slug='integer_default',
            primitive_type='integer')
        question1 = TextField(name="entity_question", code="q1", label="What is associated entity",
            entity_question_flag=True, ddtype=string_type)
        question2 = IntegerField(name="question1_Name", code="q2", label="What is your name",
            constraints=[NumericRangeConstraint(min=10, max=100)],
            ddtype=integer_type)
        return FormModel(self.dbm, entity_type=["clinic"], name="aids", label="Aids form_model",
            form_code="aids", type=['survey'], fields=[question1, question2])

    #TODO : Need to add validations for incompatible data types -> eg. string for number. This validation is hadled outside the service for now.
    def test_edit_survey_response_when_fields_constraints_are_not_satisfied(self):
        survey_response = Mock(spec=SurveyResponse)
        with patch('mangrove.datastore.entity.by_short_code') as get_entity:
            with patch('mangrove.transport.services.survey_response_service.get_form_model_by_code') as get_form_model:
                get_entity.return_value = Mock(spec=Entity)
                get_form_model.return_value = self.form_model()
                transport_info = TransportInfo('web', 'src', 'dest')
                values = {'form_code': 'aids', 'q1': 'a1', 'q2': '200'}

                request = Request(values, transport_info)
                response = self.survey_response_service.edit_survey('aids', values, [], transport_info, request.message,
                    survey_response)
                self.assertFalse(response.success)
                self.assertEquals('aids', response.form_code)
                self.assertEquals(OrderedDict([('q2', u'Answer 200 for question q2 is greater than allowed.')]),
                    response.errors)
                self.assertEquals(['clinic'], response.entity_type)
                self.assertEquals(OrderedDict([('q1', 'a1')]), response.processed_data)
                self.assertIsNotNone(response.submission_id)

                assert not survey_response.update.called


class TestSurveyResponseServiceIT(MangroveTestCase):
    def test_survey_response_is_saved(self):
        test_data = TestData(self.manager)
        survey_response_service = SurveyResponseService(self.manager)

        values = {'ID': test_data.entity1.short_code, 'Q1': 'name', 'Q2': '80', 'Q3': 'a'}
        transport_info = TransportInfo('web', 'src', 'dest')
        request = Request(values, transport_info)
        response = survey_response_service.save_survey('CL1', values, [], transport_info,
            request.message)

        self.assertTrue(response.success)
        self.assertEqual(0, response.errors.__len__())
        self.assertIsNotNone(response.datarecord_id)
        self.assertIsNotNone(response.survey_response_id)
        self.assertEqual(test_data.entity_type, response.entity_type)
        self.assertEqual('CL1', response.form_code)
        self.assertEqual('1', response.short_code)
        self.assertDictEqual(OrderedDict([('Q1', 'name'), ('Q3', ['RED']), ('Q2', 80), ('ID', u'1')]),
            response.processed_data)

        submission = Submission.get(self.manager, response.survey_response_id)
        self.assertDictEqual({'Q1': 'name', 'Q3': 'a', 'Q2': '80', 'ID': '1'}, submission.values)
        self.assertEqual(test_data.form_model.revision, submission.form_model_revision)
        self.assertEqual(test_data.entity1.short_code, submission.get_entity_short_code('ID'))
        self.assertEqual(True, submission.status)
        self.assertIsNotNone(submission.data_record)

        survey_response = SurveyResponse.get(self.manager, response.survey_response_id)
        self.assertDictEqual({'Q1': 'name', 'Q3': 'a', 'Q2': '80', 'ID': '1'}, survey_response.values)
        self.assertDictEqual({'Q1': 'name', 'Q3': 'a', 'Q2': '80', 'ID': '1'}, survey_response.values)
        self.assertEqual(test_data.form_model.revision, survey_response.form_model_revision)
        self.assertEqual(True, survey_response.status)
        self.assertIsNotNone(survey_response.data_record)

    def test_survey_response_is_edited_and_new_submission_and_datarecord_is_created(self):
        test_data = TestData(self.manager)
        survey_response_service = SurveyResponseService(self.manager)

        values = {'ID': test_data.entity1.short_code, 'Q1': 'name', 'Q2': '80', 'Q3': 'a'}
        transport_info = TransportInfo('web', 'src', 'dest')
        request = Request(values, transport_info)

        saved_response = survey_response_service.save_survey('CL1', values, [], transport_info, request.message)
        self.assertDictEqual(OrderedDict([('Q1', 'name'), ('Q3', ['RED']), ('Q2', 80), ('ID', u'1')]),
            saved_response.processed_data)

        new_values = {'ID': test_data.entity1.short_code, 'Q1': 'new_name', 'Q2': '430', 'Q3': 'b'}
        survey_response_to_edit = SurveyResponse.get(self.manager, saved_response.survey_response_id)
        edited_response = survey_response_service.edit_survey('CL1', new_values, [], transport_info, request.message,
            survey_response_to_edit)

        self.assertTrue(edited_response.success)
        self.assertEqual(0, edited_response.errors.__len__())
        self.assertIsNotNone(edited_response.datarecord_id)
        self.assertIsNotNone(edited_response.survey_response_id)
        self.assertEqual(test_data.entity_type, edited_response.entity_type)
        self.assertEqual('CL1', edited_response.form_code)
        self.assertEqual('1', edited_response.short_code)
        self.assertDictEqual(OrderedDict([('Q1', 'new_name'), ('Q3', ['YELLOW']), ('Q2', 430), ('ID', u'1')]),
            edited_response.processed_data)

        submission = Submission.get(self.manager, edited_response.submission_id)
        self.assertNotEquals(saved_response.submission_id, edited_response.submission_id)
        self.assertIsNotNone(submission.form_model_revision)
        self.assertDictEqual({'Q1': 'new_name', 'Q3': 'b', 'Q2': '430', 'ID': '1'}, submission.values)

        self.assertNotEquals(saved_response.datarecord_id, edited_response.datarecord_id)

        old_data_record = DataRecord.get(self.manager, saved_response.datarecord_id)
        self.assertTrue(old_data_record.voided)
        new_data_record = DataRecord.get(self.manager, edited_response.datarecord_id)
        self.assertFalse(new_data_record.voided)

        edited_survey_response = SurveyResponse.get(self.manager, edited_response.survey_response_id)
        self.assertEquals(1, len(edited_survey_response._doc.data_record_history))
        self.assertEquals(old_data_record.id, edited_survey_response._doc.data_record_history[0])