from unittest import TestCase, SkipTest
from mangrove.transport.survey_responses import SurveyResponse
from mock import Mock, patch
from errors.MangroveException import MangroveException
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.field import TextField
from mangrove.datastore.entity import Entity
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.form_model import FormModel
from mangrove.form_model.forms import EditSurveyResponseForm

class TestEditSurveyResponseForm(TestCase):
    def test_save_updates_survey_response_and_entity(self):
        dbm = Mock(spec=DatabaseManager)
        ddtype = DataDictType(dbm, name='Default String Datadict Type', slug='string_default',
            primitive_type='string')
        question1 = TextField(name="entity_question", code="q1", label="What is associated entity",
            entity_question_flag=True, ddtype=ddtype)
        question2 = TextField(name="question1_Name", code="q2", label="What is your name",
            defaultValue="some default value", ddtype=ddtype)
        values = {'q1': question1, 'q2': question2}

        survey_response = Mock(spec=SurveyResponse)
        form_model = Mock(spec=FormModel)
        dictionary = {'q1': 'a1', 'q2': 'a2'}
        entity = Mock(spec=Entity)
        with patch('mangrove.form_model.forms.get_by_short_code') as get_by_short_code_mock:
            get_by_short_code_mock.return_value = entity
            form_model.validate_submission.return_value = dictionary, ''
            form_model._get_field_by_code.side_effect = lambda arg: values[arg]

            form = EditSurveyResponseForm(dbm, survey_response, form_model, dictionary)
            form.save()

            expected_data = [('entity_question', 'a1', ddtype), ('question1_Name', 'a2', ddtype)]
            survey_response.update.assert_called_once_with(form_model, expected_data, entity)
            entity.update_latest_data.assert_called_once_with(data=expected_data)
            survey_response.set_status.assert_called_once_with('')


    @SkipTest
    def test_set_status_even_if_exception_occurs_during_updates(self):
        dbm = Mock(spec=DatabaseManager)
        ddtype = DataDictType(dbm, name='Default String Datadict Type', slug='string_default',
            primitive_type='string')
        question1 = TextField(name="entity_question", code="q1", label="What is associated entity",
            entity_question_flag=True, ddtype=ddtype)
        question2 = TextField(name="question1_Name", code="q2", label="What is your name",
            defaultValue="some default value", ddtype=ddtype)
        values = {'q1': question1, 'q2': question2}

        survey_response = Mock(spec=SurveyResponse)
        form_model = Mock(spec=FormModel)
        dictionary = {'q1': 'a1', 'q2': 'a2'}
        entity = Mock(spec=Entity)
        with patch('mangrove.form_model.forms.get_by_short_code') as get_by_short_code_mock:
            get_by_short_code_mock.return_value = entity
            form_model.validate_submission.return_value = dictionary, ''
            form_model._get_field_by_code.side_effect = lambda arg: values[arg]
            survey_response.update.side_effect = ValueError('an exception message')

            self.assertRaises(MangroveException)
            form = EditSurveyResponseForm(dbm, survey_response, form_model, dictionary)
            form.save()

            expected_data = [('entity_question', 'a1', ddtype), ('question1_Name', 'a2', ddtype)]
            survey_response.update.assert_called_once_with(form_model, expected_data, entity)
            entity.update_latest_data.assert_called_once_with(data=expected_data)
            survey_response.set_status.assert_called_once_with('an exception message')
