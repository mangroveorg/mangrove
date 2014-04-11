from unittest import TestCase
from mangrove.transport.contract.transport_info import TransportInfo
from mock import Mock, patch, MagicMock
from mangrove.datastore.documents import EntityDocument
from mangrove.form_model.field import TextField, UniqueIdField
from mangrove.datastore.entity import Entity
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.form_model import FormModel
from mangrove.form_model.forms import EditSurveyResponseForm
from mangrove.transport.contract.survey_response import SurveyResponse

class TestEditSurveyResponseForm(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)

    def test_valid_edit_survey_response_form(self):
        question1 = UniqueIdField('some_entity_type',name="entity_question", code="q1", label="What is associated entity")
        question2 = TextField(name="question1_Name", code="q2", label="What is your name",
            defaultValue="some default value")
        values = {'q1': question1, 'q2': question2}

        survey_response = Mock(spec=SurveyResponse)
        form_model = Mock(spec=FormModel)
        dictionary = {'q1': 'a1', 'q2': 'a2'}
        form_model.validate_submission.return_value = dictionary, ''
        form_model.get_field_by_code.side_effect = lambda arg: values[arg]
        form_model.entity_questions = [question1]
        form = EditSurveyResponseForm(self.dbm, survey_response, form_model, dictionary)
        form.save()

        expected_data = [('entity_question', 'a1'), ('question1_Name', 'a2')]
        survey_response.update.assert_called_once_with(form_model, expected_data)
        #entity.update_latest_data.assert_called_once_with(data=expected_data)
        survey_response.set_status.assert_called_once_with('')

    def test_edit_survey_response_form_with_invalid_data(self):
        question1 = UniqueIdField('clinic',name="entity_question", code="q1", label="What is associated entity")
        question2 = TextField(name="question1_Name", code="q2", label="What is your name",
            defaultValue="some default value")
        values = {'q1': question1, 'q2': question2}

        survey_response = Mock(spec=SurveyResponse)
        form_model = MagicMock(spec=FormModel)
        dictionary = {'q1': 'a1', 'q2': 1}
        # entity = Mock(spec=Entity)
        # with patch('mangrove.form_model.forms.get_by_short_code') as get_by_short_code_mock:
        #     get_by_short_code_mock.return_value = entity
        form_model.validate_submission.return_value = dictionary, 'error'
        form_model.get_field_by_code.side_effect = lambda arg: values[arg]

        form = EditSurveyResponseForm(self.dbm, survey_response, form_model, dictionary)

        self.assertFalse(form.is_valid)
        self.assertEquals(form.errors, 'error')

    def test_edit_survey_response_form_for_previously_errored_survey_response(self):
        question1 = UniqueIdField('patient',name="entity_question", code="q1", label="What is associated entity")
        question2 = TextField(name="question1_Name", code="q2", label="What is your name",
            defaultValue="some default value")
        form_model = FormModel(self.dbm, name="aids", label="Aids form_model",
            form_code="clinic", fields=[question1, question2])

        errored_survey_response = self.errored_survey_response()
        form = EditSurveyResponseForm(self.dbm, errored_survey_response, form_model, {'q1': 'a1', 'q2': 'a2'})
        form.save()
        self.assertTrue(form.is_valid)

    def test_edit_survey_response_form_with_missing_data(self):
        question1 = UniqueIdField('entity_type',name="entity_question", code="q1", label="What is associated entity")
        question2 = TextField(name="question1_Name", code="q2", label="What is your name",
            defaultValue="some default value")
        values = {'q1': question1, 'q2': question2}

        survey_response = Mock(spec=SurveyResponse)
        form_model = Mock(spec=FormModel)
        dictionary = {'q1': 'a1'}
        # entity = Mock(spec=Entity)
        # with patch('mangrove.form_model.forms.get_by_short_code') as get_by_short_code_mock:
        #     get_by_short_code_mock.return_value = entity

        form_model.validate_submission.return_value = dictionary, 'error'
        form_model.get_field_by_code.side_effect = lambda arg: values[arg]
        form_model.entity_questions = [question1]
        # form_model.entity_type = entity
        form = EditSurveyResponseForm(self.dbm, survey_response, form_model, dictionary)
        self.assertFalse(form.is_valid)
        self.assertEquals(form.errors, 'error')

    def test_save_of_edit_survey_response_form_with_invalid_data(self):
        question1 = UniqueIdField('entity_type',name="entity_question", code="q1", label="What is associated entity")
        question2 = TextField(name="question1_Name", code="q2", label="What is your name",
            defaultValue="some default value")
        values = {'q1': question1, 'q2': question2}

        survey_response = Mock(spec=SurveyResponse)
        form_model = Mock(spec=FormModel)
        dictionary = {'q1': 'a1', 'q2': 1}
        entity = Mock(spec=Entity)
        # with patch('mangrove.form_model.forms.get_by_short_code') as get_by_short_code_mock:
        #     get_by_short_code_mock.return_value = entity
        form_model.validate_submission.return_value = dictionary, 'error'
        form_model.get_field_by_code.side_effect = lambda arg: values[arg]
        form_model.entity_questions = [question1]
        form = EditSurveyResponseForm(self.dbm, survey_response, form_model, dictionary)
        form.entity_type = entity
        self.assertRaises(AssertionError, form.save)
        self.assertFalse(form.saved)

        assert not survey_response.update.called
        assert not entity.update_latest_data.called

    def errored_survey_response(self):
        survey_response = SurveyResponse(self.dbm, TransportInfo('web', 'web', 'web'), form_code="clinic")
        survey_response.set_status('previous error')
        return survey_response