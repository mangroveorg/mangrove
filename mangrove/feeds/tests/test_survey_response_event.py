import trace
from unittest import TestCase
from mock import Mock, PropertyMock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.field import SelectField, DateField, TextField, IntegerField
from mangrove.form_model.form_model import FormModel
from mangrove.feeds.survey_response_event import SurveyResponseEventBuilder
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

            builder = SurveyResponseEventBuilder(None, self.survey_response, self.form_model, 'rep1', {})
            builder.event_document()
            self.fail('Since We dont have the correct values for options this should raised an exception')
        except Exception as e:
            self.assertEqual('Survey Response Id : someid, field code q1, value not found for selected choice b',
                             e.message)


    def test_format_is_present_for_date_fields(self):
        value_mock = PropertyMock(return_value={'q3': '21.03.2011'})
        type(self.survey_response).values = value_mock

        builder = SurveyResponseEventBuilder(None, self.survey_response, self.form_model,'rep1', {})
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

        builder = SurveyResponseEventBuilder(None, self.survey_response, self.form_model,'rep1', {})
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

        builder = SurveyResponseEventBuilder(None, self.survey_response, self.form_model, 'rep1', {})
        dictionary = builder._create_answer_dictionary(select_field)
        self.assertEquals({'b': 'mango'}, dictionary.get('answer'))
        self.assertEquals('select', dictionary.get('label'))
        self.assertEquals('select1', dictionary.get('type'))


    def test_question_code_case_mismatch_gives_right_value(self):
        value_mock = PropertyMock(return_value={'Q4': '23'})
        type(self.survey_response).values = value_mock
        number_field = IntegerField('name', 'q4', 'age', self.ddtype)

        builder = SurveyResponseEventBuilder(None, self.survey_response, self.form_model, 'rep1', {})
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
        builder = SurveyResponseEventBuilder(self.dbm, self.survey_response, self.form_model, 'rep1', {})

        with patch('mangrove.feeds.survey_response_event.get_subject_name') as get_subject_name:
            get_subject_name.return_value = 'Kormanagala Clinic'

            dictionary = builder._create_answer_dictionary(subject_field)

            self.assertEquals({'cli001': 'Kormanagala Clinic'}, dictionary.get('answer'))
            self.assertEquals('Reporting for Subject', dictionary.get('label'))
            self.assertEquals('text', dictionary.get('type'))
            self.assertEquals('true', dictionary.get('is_entity_question'))


    def test_data_sender_answer_has_code_only(self):
        value_mock = PropertyMock(return_value={'Q1': 'rep023'})
        type(self.survey_response).values = value_mock
        data_sender_field = TextField('name', 'q1', 'Reporting on Behalf of', self.ddtype, entity_question_flag=True)
        type(self.form_model).entity_question = PropertyMock(return_value=data_sender_field)
        type(self.form_model).entity_type = PropertyMock(return_value='reporter')
        builder = SurveyResponseEventBuilder(self.dbm, self.survey_response, self.form_model, 'rep023', {})
        dictionary = builder._create_answer_dictionary(data_sender_field)

        self.assertEquals('rep023', dictionary.get('answer'))
        self.assertEquals('Reporting on Behalf of', dictionary.get('label'))
        self.assertEquals('text', dictionary.get('type'))
        self.assertEquals('true', dictionary.get('is_entity_question'))

    def test_override_data_sender_info(self):
        value_mock = PropertyMock(return_value={'Q1': 'rep023'})
        type(self.survey_response).values = value_mock
        data_sender_field = TextField('name', 'q1', 'Reporting on Behalf of', self.ddtype, entity_question_flag=True)
        type(self.form_model).entity_question = PropertyMock(return_value=data_sender_field)
        type(self.form_model).entity_type = PropertyMock(return_value='reporter')

        self.form_model.fields = [data_sender_field]

        with patch('mangrove.feeds.survey_response_event.get_subject_name') as get_subject_name:
            get_subject_name.return_value = 'real data sender'
            builder = SurveyResponseEventBuilder(self.dbm, self.survey_response, self.form_model, 'rep12', {})
            doc = builder.event_document()

            get_subject_name.assert_called_once_with(self.dbm, ['reporter'], 'rep12')

            self.assertDictEqual({'id': 'rep12', 'name': 'real data sender'}, doc.data_sender)
