from unittest import TestCase
from mock import Mock, PropertyMock
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.field import SelectField, DateField
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
            value_mock = PropertyMock(return_value={'q1': 'ba'})
            type(self.survey_response).values = value_mock

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
