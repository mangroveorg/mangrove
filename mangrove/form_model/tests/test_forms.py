from unittest import TestCase
from mangrove.transport.contract.transport_info import TransportInfo
from mock import Mock, patch
from mangrove.datastore.datadict import DataDictType
from mangrove.datastore.documents import EntityDocument
from mangrove.form_model.field import TextField
from mangrove.datastore.entity import Entity
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.form_model import FormModel
from mangrove.form_model.forms import EditSurveyResponseForm
from mangrove.transport.contract.survey_response import SurveyResponse

class TestEditSurveyResponseForm(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)

    def test_valid_edit_survey_response_form(self):
        ddtype = DataDictType(self.dbm, name='Default String Datadict Type', slug='string_default',
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

            form = EditSurveyResponseForm(self.dbm, survey_response, form_model, dictionary)
            form.save()

            expected_data = [('entity_question', 'a1', ddtype), ('question1_Name', 'a2', ddtype)]
            survey_response.update.assert_called_once_with(form_model, expected_data, entity)
            entity.update_latest_data.assert_called_once_with(data=expected_data)
            survey_response.set_status.assert_called_once_with('')

    def test_edit_survey_response_form_with_invalid_data(self):
        ddtype = DataDictType(self.dbm, name='Default String Datadict Type', slug='string_default',
            primitive_type='string')
        question1 = TextField(name="entity_question", code="q1", label="What is associated entity",
            entity_question_flag=True, ddtype=ddtype)
        question2 = TextField(name="question1_Name", code="q2", label="What is your name",
            defaultValue="some default value", ddtype=ddtype)
        values = {'q1': question1, 'q2': question2}

        survey_response = Mock(spec=SurveyResponse)
        form_model = Mock(spec=FormModel)
        dictionary = {'q1': 'a1', 'q2': 1}
        entity = Mock(spec=Entity)
        with patch('mangrove.form_model.forms.get_by_short_code') as get_by_short_code_mock:
            get_by_short_code_mock.return_value = entity
            form_model.validate_submission.return_value = dictionary, 'error'
            form_model._get_field_by_code.side_effect = lambda arg: values[arg]

            form = EditSurveyResponseForm(self.dbm, survey_response, form_model, dictionary)

            self.assertFalse(form.is_valid)
            self.assertEquals(form.errors, 'error')

    def test_edit_survey_response_form_for_previously_errored_survey_response(self):
        ddtype = DataDictType(self.dbm, name='Default String Datadict Type', slug='string_default',
            primitive_type='string')
        question1 = TextField(name="entity_question", code="q1", label="What is associated entity",
            entity_question_flag=True, ddtype=ddtype)
        question2 = TextField(name="question1_Name", code="q2", label="What is your name",
            defaultValue="some default value", ddtype=ddtype)
        form_model = FormModel(self.dbm, entity_type=['patient'], name="aids", label="Aids form_model",
            form_code="clinic", type='survey', fields=[question1, question2])

        entity = Mock(spec=Entity)
        entity._doc = Mock(spec=EntityDocument)

        errored_survey_response = self.errored_survey_response()
        with patch('mangrove.form_model.forms.get_by_short_code') as get_by_short_code_mock:
            get_by_short_code_mock.return_value = entity

            form = EditSurveyResponseForm(self.dbm, errored_survey_response, form_model, {'q1': 'a1', 'q2': 'a2'})
            form.save()
            self.assertTrue(form.is_valid)

    def test_edit_survey_response_form_with_missing_data(self):
        ddtype = DataDictType(self.dbm, name='Default String Datadict Type', slug='string_default',
            primitive_type='string')
        question1 = TextField(name="entity_question", code="q1", label="What is associated entity",
            entity_question_flag=True, ddtype=ddtype)
        question2 = TextField(name="question1_Name", code="q2", label="What is your name",
            defaultValue="some default value", ddtype=ddtype)
        values = {'q1': question1, 'q2': question2}

        survey_response = Mock(spec=SurveyResponse)
        form_model = Mock(spec=FormModel)
        dictionary = {'q1': 'a1'}
        entity = Mock(spec=Entity)
        with patch('mangrove.form_model.forms.get_by_short_code') as get_by_short_code_mock:
            get_by_short_code_mock.return_value = entity
            form_model.validate_submission.return_value = dictionary, 'error'
            form_model._get_field_by_code.side_effect = lambda arg: values[arg]

            form = EditSurveyResponseForm(self.dbm, survey_response, form_model, dictionary)
            self.assertFalse(form.is_valid)
            self.assertEquals(form.errors, 'error')

    def test_save_of_edit_survey_response_form_with_invalid_data(self):
        ddtype = DataDictType(self.dbm, name='Default String Datadict Type', slug='string_default',
            primitive_type='string')
        question1 = TextField(name="entity_question", code="q1", label="What is associated entity",
            entity_question_flag=True, ddtype=ddtype)
        question2 = TextField(name="question1_Name", code="q2", label="What is your name",
            defaultValue="some default value", ddtype=ddtype)
        values = {'q1': question1, 'q2': question2}

        survey_response = Mock(spec=SurveyResponse)
        form_model = Mock(spec=FormModel)
        dictionary = {'q1': 'a1', 'q2': 1}
        entity = Mock(spec=Entity)
        with patch('mangrove.form_model.forms.get_by_short_code') as get_by_short_code_mock:
            get_by_short_code_mock.return_value = entity
            form_model.validate_submission.return_value = dictionary, 'error'
            form_model._get_field_by_code.side_effect = lambda arg: values[arg]

            form = EditSurveyResponseForm(self.dbm, survey_response, form_model, dictionary)
            self.assertRaises(AssertionError, form.save)
            self.assertFalse(form.saved)

            assert not survey_response.update.called
            assert not entity.update_latest_data.called

    def errored_survey_response(self):
        survey_response = SurveyResponse(self.dbm, TransportInfo('web', 'web', 'web'), form_code="clinic")
        survey_response.set_status('previous error')
        return survey_response