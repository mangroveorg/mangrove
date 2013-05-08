from unittest import TestCase
from mock import Mock, PropertyMock
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

    def test_raise_exception_when_value_for_selected_option_not_found(self):
        try:
            options = [{'text': 'orange', 'val': 'a'}]
            self.form_model.fields.return_value = [
                SelectField('name', 'q1', 'label', options, self.ddtype, single_select_flag=False)]
            type(self.survey_response).values = PropertyMock(return_value={'q1': 'ba'})

            builder = SurveyResponseEventBuilder(self.survey_response, self.form_model, {})
            builder.event_document()
            self.fail('Since We dont have the correct values for options this should raised an exception')
        except Exception as e:
            pass

    def test_format_is_present_for_date_fields(self):
        value_mock = PropertyMock(return_value={'q3': '21.03.2011'})
        type(self.survey_response).values = value_mock

        builder = SurveyResponseEventBuilder(self.survey_response, self.form_model, {})
        dictionary = builder._create_answer_dictionary(DateField('name', 'q3', 'date lab', 'dd.mm.yyyy', self.ddtype))
        self.assertEquals('dd.mm.yyyy', dictionary.get('format'))
        self.assertEquals('21.03.2011', dictionary.get('answer'))
        self.assertEquals('date lab', dictionary.get('label'))
        self.assertEquals('date', dictionary.get('type'))

    def test_entity_question_attribute_is_provided(self):
        value_mock = PropertyMock(return_value={'q1': 'CLI'})
        type(self.survey_response).values = value_mock
        mock_field = Mock(spec=TextField)
        type(mock_field).code = PropertyMock(return_value='q1')
        type(self.form_model).entity_question = PropertyMock(return_value=mock_field)

        builder = SurveyResponseEventBuilder(self.survey_response, self.form_model, {})
        dictionary = builder._create_answer_dictionary(
            TextField('name', 'q1', 'entity reporting on', self.ddtype, entity_question_flag=True))
        self.assertEquals('CLI', dictionary.get('answer'))
        self.assertEquals('entity reporting on', dictionary.get('label'))
        self.assertEquals('text', dictionary.get('type'))
        self.assertEquals('true', dictionary.get('is_entity_question'))

    def test_multi_select_field_value_representation(self):
        value_mock = PropertyMock(return_value={'q4': 'ac'})
        type(self.survey_response).values = value_mock
        select_field = SelectField('name', 'q4', 'multi select',
            [{'text': 'orange', 'val': 'a'}, {'text': 'mango', 'val': 'b'}, {'text': 'apple', 'val': 'c'}], self.ddtype,
            single_select_flag=False)

        builder = SurveyResponseEventBuilder(self.survey_response, self.form_model, {})
        dictionary = builder._create_answer_dictionary(select_field)
        self.assertEquals({'a': 'orange', 'c': 'apple'}, dictionary.get('answer'))
        self.assertEquals('multi select', dictionary.get('label'))
        self.assertEquals('select', dictionary.get('type'))

    def test_single_select_field_value_representation(self):
        value_mock = PropertyMock(return_value={'q4': 'b'})
        type(self.survey_response).values = value_mock
        select_field = SelectField('name', 'q4', 'select',
            [{'text': 'orange', 'val': 'a'}, {'text': 'mango', 'val': 'b'}, {'text': 'apple', 'val': 'c'}], self.ddtype)

        builder = SurveyResponseEventBuilder(self.survey_response, self.form_model, {})
        dictionary = builder._create_answer_dictionary(select_field)
        self.assertEquals({'b': 'mango'}, dictionary.get('answer'))
        self.assertEquals('select', dictionary.get('label'))
        self.assertEquals('select1', dictionary.get('type'))

    def test_question_code_case_mismatch_gives_right_value(self):
        value_mock = PropertyMock(return_value={'Q4': '23'})
        type(self.survey_response).values = value_mock
        number_field = IntegerField('name', 'q4', 'age', self.ddtype)

        builder = SurveyResponseEventBuilder(self.survey_response, self.form_model, {})
        dictionary = builder._create_answer_dictionary(number_field)
        self.assertEquals('23', dictionary.get('answer'))
        self.assertEquals('age', dictionary.get('label'))
        self.assertEquals('integer', dictionary.get('type'))

