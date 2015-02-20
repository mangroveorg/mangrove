from datetime import datetime
from unittest import TestCase
from mock import Mock, PropertyMock, patch
from mangrove.datastore.documents import SurveyResponseDocument
from mangrove.datastore.entity import Entity
from mangrove.datastore.database import DatabaseManager
from mangrove.errors.MangroveException import DataObjectNotFound
from mangrove.form_model.field import SelectField, DateField, TextField, IntegerField, UniqueIdField
from mangrove.form_model.form_model import FormModel
from mangrove.feeds.enriched_survey_response import EnrichedSurveyResponseBuilder
from mangrove.transport.contract.survey_response import SurveyResponse


class TestSurveyResponseEventBuilder(TestCase):
    def setUp(self):
        self.survey_response = Mock(spec=SurveyResponse)
        self.form_model = Mock(spec=FormModel)
        self.dbm = Mock(spec=DatabaseManager)


    def test_format_is_present_for_date_fields(self):
        value_mock = PropertyMock(return_value={'q3': '21.03.2011'})
        type(self.survey_response).values = value_mock

        builder = EnrichedSurveyResponseBuilder(None, self.survey_response, self.form_model, {})
        dictionary = builder._create_answer_dictionary(DateField('name', 'q3', 'date lab', 'dd.mm.yyyy'))
        self.assertEquals('dd.mm.yyyy', dictionary.get('format'))
        self.assertEquals('21.03.2011', dictionary.get('answer'))
        self.assertEquals('date lab', dictionary.get('label'))
        self.assertEquals('date', dictionary.get('type'))


    def test_multi_select_field_value_representation(self):
        value_mock = PropertyMock(return_value={'q4': 'ac'})
        type(self.survey_response).values = value_mock
        select_field = SelectField('name', 'q4', 'multi select',
                                   [{'text': 'orange', 'val': 'a'}, {'text': 'mango', 'val': 'b'},
                                    {'text': 'apple', 'val': 'c'}],
                                   single_select_flag=False)

        builder = EnrichedSurveyResponseBuilder(None, self.survey_response, self.form_model, {})
        dictionary = builder._create_answer_dictionary(select_field)
        self.assertEquals({'a': 'orange', 'c': 'apple'}, dictionary.get('answer'))
        self.assertEquals('multi select', dictionary.get('label'))
        self.assertEquals('select', dictionary.get('type'))


    def test_single_select_field_value_representation(self):
        value_mock = PropertyMock(return_value={'q4': 'b'})
        type(self.survey_response).values = value_mock
        select_field = SelectField('name', 'q4', 'select',
                                   [{'text': 'orange', 'val': 'a'}, {'text': 'mango', 'val': 'b'},
                                    {'text': 'apple', 'val': 'c'}])

        builder = EnrichedSurveyResponseBuilder(None, self.survey_response, self.form_model, {})
        dictionary = builder._create_answer_dictionary(select_field)
        self.assertEquals({'b': 'mango'}, dictionary.get('answer'))
        self.assertEquals('select', dictionary.get('label'))
        self.assertEquals('select1', dictionary.get('type'))


    def test_question_code_case_mismatch_gives_right_value(self):
        value_mock = PropertyMock(return_value={'Q4': '23'})
        type(self.survey_response).values = value_mock
        number_field = IntegerField('name', 'q4', 'age')

        builder = EnrichedSurveyResponseBuilder(None, self.survey_response, self.form_model, {})
        dictionary = builder._create_answer_dictionary(number_field)
        self.assertEquals('23', dictionary.get('answer'))
        self.assertEquals('age', dictionary.get('label'))
        self.assertEquals('integer', dictionary.get('type'))


    def test_subject_answer_has_name_of_subject(self):
        value_mock = PropertyMock(return_value={'Q1': 'cli001'})
        type(self.survey_response).values = value_mock
        subject_field = UniqueIdField('clinic','name', 'q1', 'Reporting for Subject')
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, {})

        with patch('mangrove.feeds.enriched_survey_response.by_short_code') as by_short_code:
            entity = Mock(spec=Entity)
            by_short_code.return_value = entity
            type(entity).data = PropertyMock(return_value={'name': {'value': 'Kormanagala Clinic'}})

            dictionary = builder._create_answer_dictionary(subject_field)

            self.assertEquals({'id': 'cli001', 'name': 'Kormanagala Clinic', 'deleted': False},
                              dictionary.get('answer'))
            self.assertEquals('Reporting for Subject', dictionary.get('label'))
            self.assertEquals('unique_id', dictionary.get('type'))
            self.assertEquals('true', dictionary.get('is_entity_question'))

    def test_subject_answer_id_as_value_rather_than_name_when_subject_is_not_existing(self):
        survey_response = Mock(spec=SurveyResponse)
        type(survey_response).values = PropertyMock(return_value={'q1': 'cli001'})
        subject_field = UniqueIdField('clinic','name', 'q1', 'Reporting for Subject')
        builder = EnrichedSurveyResponseBuilder(self.dbm, survey_response, self.form_model, {})

        with patch('mangrove.feeds.enriched_survey_response.by_short_code') as by_short_code:
            by_short_code.side_effect = DataObjectNotFound("Entity", "id", "cli001")

            dictionary = builder._create_answer_dictionary(subject_field)

            self.assertEquals({'id': 'cli001', 'name': '', 'deleted': True}, dictionary.get('answer'))
            self.assertEquals('Reporting for Subject', dictionary.get('label'))
            self.assertEquals('unique_id', dictionary.get('type'))
            self.assertEquals('true', dictionary.get('is_entity_question'))


    def test_delete_status_updated(self):
        type(self.survey_response).status = PropertyMock(return_value=True)
        self.survey_response.is_void.return_value = True
        type(self.survey_response).values = PropertyMock(return_value={})
        type(self.survey_response).modified = PropertyMock(return_value=datetime.now())
        type(self.form_model).fields = PropertyMock(return_value=[])
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, {})

        def patch_data_sender():
            return {}

        builder._data_sender = patch_data_sender
        doc = builder.feed_document()

        self.assertTrue(doc.void)

    def test_status_is_success_for_valid_non_deleted_survey_response(self):
        type(self.survey_response).status = PropertyMock(return_value=True)
        self.survey_response.is_void.return_value = False
        type(self.survey_response).values = PropertyMock(return_value={'q1': 'something'})
        type(self.survey_response).modified = PropertyMock(return_value=datetime.now())
        field = TextField('name', 'q1', 'A Question')
        type(self.form_model).fields = PropertyMock(return_value=[field])
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, {})

        def patch_data_sender():
            return {}

        builder._data_sender = patch_data_sender
        doc = builder.feed_document()

        self.assertEqual('success', doc.status)
        self.assertFalse(doc.void)

    def test_status_is_error_for_invalid_not_deleted_survey_response(self):
        type(self.survey_response).status = PropertyMock(return_value=False)
        self.survey_response.is_void.return_value = False
        type(self.survey_response).values = PropertyMock(return_value={})
        type(self.survey_response).modified = PropertyMock(return_value=datetime.now())
        field = TextField('name', 'q1', 'A Question')
        type(self.form_model).fields = PropertyMock(return_value=[field])
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, {})

        def patch_data_sender():
            return {}

        builder._data_sender = patch_data_sender
        doc = builder.feed_document()

        self.assertEqual('error', doc.status)
        self.assertFalse(doc.void)

    def test_field_values_not_calculated_when_submission_is_error(self):
        type(self.survey_response).status = PropertyMock(return_value=False)
        type(self.survey_response).values = PropertyMock(return_value={'q1': '1', 'q2': 'abc'})
        type(self.survey_response).modified = PropertyMock(return_value=datetime.now())
        fields_property_mock = PropertyMock(return_value={})
        type(self.form_model).fields = fields_property_mock
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, {})

        def patch_data_sender():
            return {}

        builder._data_sender = patch_data_sender
        doc = builder.feed_document()

        self.assertFalse(fields_property_mock.called)
        self.assertDictEqual({'q1': '1', 'q2': 'abc'}, doc.values)


    def test_identify_multi_select_answer_with_more_than_26_options(self):
        value_mock = PropertyMock(return_value={'q4': '1a1c'})
        type(self.survey_response).values = value_mock
        select_field = SelectField('name', 'q4', 'multi select',
                                   [{'text': 'orange', 'val': '1a'},
                                    {'text': 'watermelon', 'val': '1b'},
                                    {'text': 'strawberry', 'val': '1c'},
                                    {'text': 'apple', 'val': 'c'}],
                                   single_select_flag=False)

        builder = EnrichedSurveyResponseBuilder(None, self.survey_response, self.form_model, {})
        dictionary = builder._create_answer_dictionary(select_field)
        self.assertEquals({'1a': 'orange', '1c': 'strawberry'}, dictionary.get('answer'))
        self.assertEquals('multi select', dictionary.get('label'))
        self.assertEquals('select', dictionary.get('type'))

    def test_update_enriched_survey_response_with_new_survey_response_values(self):
        field = TextField('name', 'q1', 'A Question')
        type(self.form_model).fields = PropertyMock(return_value=[field])

        type(self.form_model).entity_type = PropertyMock(return_value=['reporter'])

        self.form_model.id= 'form_model_id'
        survey_response = SurveyResponse(Mock())
        survey_response._doc = SurveyResponseDocument(status=False, values={'q1': 'answer1'},
                                                      form_model_id='form_model_id')
        builder = EnrichedSurveyResponseBuilder(self.dbm, survey_response, self.form_model, {})

        def patch_data_sender():
            return {}

        builder._data_sender = patch_data_sender
        doc = builder.feed_document()

        self.assertEquals(doc.values, {'q1': 'answer1'})

        edited_survey_response_doc = SurveyResponseDocument(status=True, values={'q1': 'answer2'},
                                                            form_model_id='form_model_id')
        edited_survey_response = SurveyResponse(Mock())
        edited_survey_response._doc = edited_survey_response_doc

        new_builder = EnrichedSurveyResponseBuilder(self.dbm, edited_survey_response, self.form_model, {})
        new_builder._data_sender = patch_data_sender
        feeds_dbm = Mock(spec=DatabaseManager)
        with patch('mangrove.feeds.enriched_survey_response.get_feed_document_by_id') as get_document:
            get_document.return_value = doc
            edited_doc = new_builder.update_event_document(feeds_dbm)
            self.assertEquals(edited_doc.values, {'q1': {'answer': 'answer2', 'label': 'A Question', 'type': 'text'}})

    def test_datasender_info(self):
        survey_response = Mock(spec=SurveyResponse)
        type(survey_response).owner_uid = PropertyMock(return_value='data_sender_uid')
        type(survey_response).values = PropertyMock(return_value={})
        with patch("mangrove.feeds.enriched_survey_response.Contact.get") as get_datasender:
            data_sender = Mock(spec=Entity)
            get_datasender.return_value = data_sender
            type(data_sender).data = PropertyMock(
                return_value={"name": {"value": "data sender name"}, "mobile_number": {"value": "+39882773662"}})
            type(data_sender).short_code = PropertyMock(return_value="rep2423")
            data_sender.is_void.return_value = False
            type(self.form_model).fields = PropertyMock(return_value=[])

            builder = EnrichedSurveyResponseBuilder(self.dbm, survey_response, self.form_model, {})
            datasender_dict = builder._data_sender()

            self.assertEquals(datasender_dict.get('id'), 'rep2423')
            self.assertEquals(datasender_dict.get('last_name'), 'data sender name')
            self.assertEquals(datasender_dict.get('mobile_number'), '+39882773662')
            self.assertEquals(datasender_dict.get('question_code'), '')
            self.assertFalse(datasender_dict.get('deleted'))
            get_datasender.assert_called_once_with(self.dbm, 'data_sender_uid')

    def test_feed_datasender_is_none_when_migrating_survey_response_with_document_for_owner_id_not_found(self):
        survey_response = Mock(spec=SurveyResponse)
        type(survey_response).owner_uid = PropertyMock(return_value='data_sender_uid')
        type(survey_response).values = PropertyMock(return_value={})
        builder = EnrichedSurveyResponseBuilder(self.dbm, survey_response, self.form_model, {})
        with patch("mangrove.feeds.enriched_survey_response.Contact.get") as get_datasender:
            get_datasender.side_effect = DataObjectNotFound(Entity.__name__, 'id', None)
            data_sender = builder._data_sender()
            self.assertIsNone(data_sender['id'])
            self.assertIsNone(data_sender['last_name'])
            self.assertIsNone(data_sender['mobile_number'])
            self.assertIsNone(data_sender['deleted'])
            self.assertIsNone(data_sender['question_code'])
