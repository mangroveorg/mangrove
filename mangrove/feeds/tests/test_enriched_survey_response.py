from datetime import datetime
from unittest import TestCase
from mock import Mock, PropertyMock, patch
from mangrove.datastore.documents import  SurveyResponseDocument
from mangrove.datastore.entity import Entity
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType
from mangrove.errors.MangroveException import DataObjectNotFound
from mangrove.form_model.field import SelectField, DateField, TextField, IntegerField
from mangrove.form_model.form_model import FormModel
from mangrove.feeds.enriched_survey_response import EnrichedSurveyResponseBuilder
from mangrove.transport.contract.survey_response import SurveyResponse


class TestSurveyResponseEventBuilder(TestCase):
    def setUp(self):
        self.survey_response = Mock(spec=SurveyResponse)
        self.form_model = Mock(spec=FormModel)
        self.ddtype = Mock(spec=DataDictType)
        self.dbm = Mock(spec=DatabaseManager)

    def test_raise_exception_when_value_for_selected_option_not_found(self):
        try:
            options = [{'text': 'orange', 'val': 'a'}]

            self.form_model.fields = [
                SelectField('name', 'q1', 'label', options, self.ddtype, single_select_flag=False)]
            type(self.survey_response).values = PropertyMock(return_value={'q1': 'ba'})
            self.survey_response.id = 'someid'

            builder = EnrichedSurveyResponseBuilder(None, self.survey_response, self.form_model, 'rep1', {})
            builder.feed_document()
            self.fail('Since We dont have the correct values for options this should raised an exception')
        except Exception as e:
            self.assertEqual(
                'Survey Response Id : someid, field code q1, number of values not equal to number of selected choices: ba',
                e.message)


    def test_format_is_present_for_date_fields(self):
        value_mock = PropertyMock(return_value={'q3': '21.03.2011'})
        type(self.survey_response).values = value_mock

        builder = EnrichedSurveyResponseBuilder(None, self.survey_response, self.form_model, 'rep1', {})
        dictionary = builder._create_answer_dictionary(DateField('name', 'q3', 'date lab', 'dd.mm.yyyy', self.ddtype))
        self.assertEquals('dd.mm.yyyy', dictionary.get('format'))
        self.assertEquals('21.03.2011', dictionary.get('answer'))
        self.assertEquals('date lab', dictionary.get('label'))
        self.assertEquals('date', dictionary.get('type'))


    def test_multi_select_field_value_representation(self):
        value_mock = PropertyMock(return_value={'q4': 'ac'})
        type(self.survey_response).values = value_mock
        select_field = SelectField('name', 'q4', 'multi select',
            [{'text': 'orange', 'val': 'a'}, {'text': 'mango', 'val': 'b'},
             {'text': 'apple', 'val': 'c'}], self.ddtype,
            single_select_flag=False)

        builder = EnrichedSurveyResponseBuilder(None, self.survey_response, self.form_model, 'rep1', {})
        dictionary = builder._create_answer_dictionary(select_field)
        self.assertEquals({'a': 'orange', 'c': 'apple'}, dictionary.get('answer'))
        self.assertEquals('multi select', dictionary.get('label'))
        self.assertEquals('select', dictionary.get('type'))


    def test_single_select_field_value_representation(self):
        value_mock = PropertyMock(return_value={'q4': 'b'})
        type(self.survey_response).values = value_mock
        select_field = SelectField('name', 'q4', 'select',
            [{'text': 'orange', 'val': 'a'}, {'text': 'mango', 'val': 'b'},
             {'text': 'apple', 'val': 'c'}], self.ddtype)

        builder = EnrichedSurveyResponseBuilder(None, self.survey_response, self.form_model, 'rep1', {})
        dictionary = builder._create_answer_dictionary(select_field)
        self.assertEquals({'b': 'mango'}, dictionary.get('answer'))
        self.assertEquals('select', dictionary.get('label'))
        self.assertEquals('select1', dictionary.get('type'))


    def test_question_code_case_mismatch_gives_right_value(self):
        value_mock = PropertyMock(return_value={'Q4': '23'})
        type(self.survey_response).values = value_mock
        number_field = IntegerField('name', 'q4', 'age', self.ddtype)

        builder = EnrichedSurveyResponseBuilder(None, self.survey_response, self.form_model, 'rep1', {})
        dictionary = builder._create_answer_dictionary(number_field)
        self.assertEquals('23', dictionary.get('answer'))
        self.assertEquals('age', dictionary.get('label'))
        self.assertEquals('integer', dictionary.get('type'))


    def test_subject_answer_has_name_of_subject(self):
        value_mock = PropertyMock(return_value={'Q1': 'cli001'})
        type(self.survey_response).values = value_mock
        subject_field = TextField('name', 'q1', 'Reporting for Subject', self.ddtype, entity_question_flag=True)
        type(self.form_model).entity_question = PropertyMock(return_value=subject_field)
        type(self.form_model).entity_type = PropertyMock(return_value='Clinic')
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, 'rep1', {})

        with patch('mangrove.feeds.enriched_survey_response.by_short_code') as by_short_code:
            entity = Mock(spec=Entity)
            by_short_code.return_value = entity
            type(entity).data = PropertyMock(return_value={'name': {'value': 'Kormanagala Clinic'}})

            dictionary = builder._create_answer_dictionary(subject_field)

            self.assertEquals({'id': 'cli001', 'name': 'Kormanagala Clinic', 'deleted': False},
                dictionary.get('answer'))
            self.assertEquals('Reporting for Subject', dictionary.get('label'))
            self.assertEquals('text', dictionary.get('type'))
            self.assertEquals('true', dictionary.get('is_entity_question'))

    def test_subject_answer_id_as_value_rather_than_name_when_subject_is_not_existing(self):
        survey_response = Mock(spec=SurveyResponse)
        type(survey_response).values = PropertyMock(return_value={'q1': 'cli001'})
        subject_field = TextField('name', 'q1', 'Reporting for Subject', self.ddtype, entity_question_flag=True)
        type(self.form_model).entity_question = PropertyMock(return_value=subject_field)
        type(self.form_model).entity_type = PropertyMock(return_value='Clinic')
        builder = EnrichedSurveyResponseBuilder(self.dbm, survey_response, self.form_model, 'rep1', {})

        with patch('mangrove.feeds.enriched_survey_response.by_short_code') as by_short_code:
            by_short_code.side_effect = DataObjectNotFound("Entity", "id", "cli001")

            dictionary = builder._create_answer_dictionary(subject_field)

            self.assertEquals({'id': 'cli001', 'name': '', 'deleted': True}, dictionary.get('answer'))
            self.assertEquals('Reporting for Subject', dictionary.get('label'))
            self.assertEquals('text', dictionary.get('type'))
            self.assertEquals('true', dictionary.get('is_entity_question'))


    def test_data_sender_answer_not_included(self):
        value_mock = PropertyMock(return_value={'Q1': 'rep023'})
        type(self.survey_response).values = value_mock
        data_sender_field = TextField('name', 'q1', 'Reporting on Behalf of', self.ddtype, entity_question_flag=True)
        type(self.form_model).fields = [data_sender_field]
        type(self.form_model).entity_question = PropertyMock(return_value=data_sender_field)
        type(self.form_model).entity_type = PropertyMock(return_value=['reporter'])
        type(self.survey_response).status = PropertyMock(return_value=True)
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, 'rep023', {})
        dictionary = builder._values()

        self.assertFalse(dictionary)

    def test_override_data_sender_info(self):
        value_mock = PropertyMock(return_value={'Q1': 'rep023'})
        type(self.survey_response).values = value_mock
        type(self.survey_response).modified = PropertyMock(return_value=datetime.now())
        data_sender_field = TextField('name', 'q1', 'Reporting on Behalf of', self.ddtype, entity_question_flag=True)
        type(self.form_model).entity_question = PropertyMock(return_value=data_sender_field)
        type(self.form_model).entity_type = PropertyMock(return_value=['reporter'])

        self.form_model.fields = [data_sender_field]

        with patch('mangrove.feeds.enriched_survey_response.by_short_code') as by_short_code:
            entity = Mock(spec=Entity)
            by_short_code.return_value = entity
            type(entity).data = PropertyMock(
                return_value={'name': {'value': 'real data sender'}, 'mobile_number': {'value': '929388193'}})

            builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, 'rep12', {})
            doc = builder.feed_document()

            by_short_code.assert_called_once_with(self.dbm, 'rep023', ['reporter'], )
            self.assertDictEqual(
                {'id': 'rep023', 'last_name': 'real data sender', 'mobile_number': '929388193', 'question_code': 'q1',
                 'deleted': False},
                doc.data_sender)

    def test_delete_status_updated(self):
        type(self.survey_response).status = PropertyMock(return_value=True)
        self.survey_response.is_void.return_value = True
        type(self.survey_response).values = PropertyMock(return_value={})
        type(self.survey_response).modified = PropertyMock(return_value=datetime.now())
        type(self.form_model).fields = PropertyMock(return_value=[])
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, 'rep12', {})

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
        field = TextField('name', 'q1', 'A Question', self.ddtype)
        type(self.form_model).fields = PropertyMock(return_value=[field])
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, 'rep12', {})

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
        field = TextField('name', 'q1', 'A Question', self.ddtype)
        type(self.form_model).fields = PropertyMock(return_value=[field])
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, 'rep12', {})

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
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, 'rep12', {})

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
             {'text': 'apple', 'val': 'c'}], self.ddtype,
            single_select_flag=False)

        builder = EnrichedSurveyResponseBuilder(None, self.survey_response, self.form_model, 'rep1', {})
        dictionary = builder._create_answer_dictionary(select_field)
        self.assertEquals({'1a': 'orange', '1c': 'strawberry'}, dictionary.get('answer'))
        self.assertEquals('multi select', dictionary.get('label'))
        self.assertEquals('select', dictionary.get('type'))

    def test_update_enriched_survey_response_with_new_survey_response_values(self):
        field = TextField('name', 'q1', 'A Question', self.ddtype)
        type(self.form_model).fields = PropertyMock(return_value=[field])

        type(self.form_model).entity_type = PropertyMock(return_value=['reporter'])

        self.form_model.form_code = 'form_code'
        survey_response = SurveyResponse(Mock())
        survey_response._doc = SurveyResponseDocument(status=False, values={'q1': 'answer1'},
            form_code='form_code')
        builder = EnrichedSurveyResponseBuilder(self.dbm, survey_response, self.form_model, 'rep12', {})

        def patch_data_sender():
            return {}

        builder._data_sender = patch_data_sender
        doc = builder.feed_document()

        self.assertEquals(doc.values, {'q1': 'answer1'})

        edited_survey_response_doc = SurveyResponseDocument(status=True, values={'q1': 'answer2'},
            form_code='form_code')
        edited_survey_response = SurveyResponse(Mock())
        edited_survey_response._doc = edited_survey_response_doc

        new_builder = EnrichedSurveyResponseBuilder(self.dbm, edited_survey_response, self.form_model, 'rep12', {})
        new_builder._data_sender = patch_data_sender
        feeds_dbm = Mock(spec=DatabaseManager)
        with patch('mangrove.feeds.enriched_survey_response.get_feed_document_by_id') as get_document:
            get_document.return_value = doc
            edited_doc = new_builder.update_event_document(feeds_dbm)
            self.assertEquals(edited_doc.values, {'q1': {'answer': 'answer2', 'label': 'A Question', 'type': 'text'}})

    def test_update_datasender_info_for_summary_reports(self):
        data_sender_field = TextField('name', 'q1', 'A Question', self.ddtype, entity_question_flag=True)
        type(self.form_model).fields = PropertyMock(return_value=[data_sender_field])
        type(self.form_model).entity_question = PropertyMock(return_value=data_sender_field)
        type(self.form_model).entity_type = PropertyMock(return_value=['reporter'])
        self.form_model.form_code = 'form_code'
        survey_response = SurveyResponse(Mock())
        survey_response._doc = SurveyResponseDocument(status=False, values={'q1': 'rep1'}, form_code='form_code')
        builder = EnrichedSurveyResponseBuilder(self.dbm, survey_response, self.form_model, 'rep12', {})

        with patch('mangrove.feeds.enriched_survey_response.by_short_code') as by_short_code:
            entity = Mock(spec=Entity)
            by_short_code.return_value = entity
            type(entity).data = PropertyMock(
                return_value={'name': {'value': 'real data sender'}, 'mobile_number': {'value': '929388193'}})
            doc = builder.feed_document()

            self.assertEquals(doc.values, {'q1': 'rep1'})
            self.assertDictEqual(doc.data_sender,
                {'id': 'rep1', 'last_name': 'real data sender', 'mobile_number': '929388193',
                 'question_code': 'q1', 'deleted': False})

            edited_survey_response_doc = SurveyResponseDocument(status=True, values={'q1': 'rep2'},
                form_code='form_code')
            edited_survey_response = SurveyResponse(Mock())
            edited_survey_response._doc = edited_survey_response_doc

            new_builder = EnrichedSurveyResponseBuilder(self.dbm, edited_survey_response, self.form_model, 'rep12', {})
            feeds_dbm = Mock(spec=DatabaseManager)
            with patch('mangrove.feeds.enriched_survey_response.get_feed_document_by_id') as get_document:
                get_document.return_value = doc

                edited_doc = new_builder.update_event_document(feeds_dbm)
                self.assertEquals(edited_doc.data_sender,
                    {'id': 'rep2', 'last_name': 'real data sender', 'mobile_number': '929388193',
                     'question_code': 'q1', 'deleted': False})

    def test_should_not_update_datasender_info_for_individual_reports(self):
        subject_field = TextField('name', 'q1', 'A Question', self.ddtype, entity_question_flag=True)
        question_field = TextField('name', 'q2', 'Another Question', self.ddtype)
        type(self.form_model).fields = PropertyMock(return_value=[subject_field, question_field])
        type(self.form_model).entity_question = PropertyMock(return_value=subject_field)
        type(self.form_model).entity_type = PropertyMock(return_value=['school'])
        self.form_model.form_code = 'form_code'
        survey_response = SurveyResponse(Mock())
        survey_response._doc = SurveyResponseDocument(status=True, values={'q1': 'sch01', 'q2': 'answer1'},
            form_code='form_code')
        builder = EnrichedSurveyResponseBuilder(self.dbm, survey_response, self.form_model, 'rep12', {})

        with patch('mangrove.feeds.enriched_survey_response.by_short_code') as by_short_code:
            entity = Mock(spec=Entity)
            by_short_code.return_value = entity
            type(entity).data = PropertyMock(
                return_value={'name': {'value': 'real data sender'}, 'mobile_number': {'value': '929388193'}})
            doc = builder.feed_document()

            self.assertDictEqual(doc.data_sender,
                {'id': 'rep12', 'last_name': 'real data sender', 'mobile_number': '929388193',
                 'question_code': '', 'deleted': False})

            edited_survey_response_doc = SurveyResponseDocument(status=True, values={'q1': 'sch02', 'q2': 'answer2'},
                form_code='form_code')
            edited_survey_response = SurveyResponse(Mock())
            edited_survey_response._doc = edited_survey_response_doc

            new_builder = EnrichedSurveyResponseBuilder(self.dbm, edited_survey_response, self.form_model, 'admin', {})
            feeds_dbm = Mock(spec=DatabaseManager)

            with patch('mangrove.feeds.enriched_survey_response.get_feed_document_by_id') as get_document:
                get_document.return_value = doc
                edited_doc = new_builder.update_event_document(feeds_dbm)
                self.assertDictEqual(edited_doc.data_sender,
                    {'id': 'rep12', 'last_name': 'real data sender', 'mobile_number': '929388193',
                     'question_code': '', 'deleted': False})

    def test_should_update_datasender_as_deleted_if_datasender_is_deleted_when_submission_is_edited(self):
        '''This use case is for individual reports'''
        type(self.survey_response).values = PropertyMock(return_value={'q1': 'ans'})
        builder = EnrichedSurveyResponseBuilder(self.dbm, self.survey_response, self.form_model, 'rep', {})
        with patch("mangrove.feeds.enriched_survey_response.by_short_code") as by_short_code:
            by_short_code.side_effect = DataObjectNotFound('Entity', 'some_id', 'value')
            sender_info_dict = builder._get_data_sender_info_dict('some_id', '')
            expected_data_sender_info = {'id': 'some_id', 'last_name': '', 'mobile_number': '', 'question_code': '',
                                         'deleted': True}
            self.assertDictEqual(expected_data_sender_info, sender_info_dict)
