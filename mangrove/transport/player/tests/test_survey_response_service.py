from collections import OrderedDict
from unittest import TestCase
from mock import Mock, patch, call
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.datastore.tests.test_data import TestData
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, InactiveFormModelException
from mangrove.form_model.form_model import FormModel
from mangrove.transport import Request, TransportInfo
from mangrove.transport.services.survey_response_service import SurveyResponseService
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from transport.submissions import Submission

class TestSurveyResponseService(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.survey_response_service = SurveyResponseService(self.dbm)

    def test_create_submission_for_a_survey_response_for_non_existent_form_code(self):
        with patch('mangrove.transport.services.survey_response_service.get_form_model_by_code') as patched_form_model:
            patched_form_model.side_effect = FormModelDoesNotExistsException('nonexistant_form_code')
            transport_info = TransportInfo('web', 'src', 'dest')
            values = {'form_code': 'nonexistant_form_code', 'q1': 'a1', 'q2': 'a2'}
            try:
                request = Request(values, transport_info)
                self.survey_response_service.save_survey_response(request)
                self.fail('Expected FormModelDoesNotExistsException')
            except FormModelDoesNotExistsException:
                pass
            calls = [call(self.dbm, 'nonexistant_form_code')]
            patched_form_model.assert_has_calls(calls)

    def test_create_submission_for_a_survey_response_for_inactive_form_code(self):
        form_model = Mock(spec=FormModel)
        with patch('mangrove.transport.services.survey_response_service.get_form_model_by_code') as patched_form_model:
            patched_form_model.return_value = form_model
            form_model.is_inactive.return_value = True
            self.dbm._save_document.return_value = SubmissionLogDocument()

            try:
                request = Request({'form_code': 'some_form_code', 'q1': 'a1', 'q2': 'a2'},
                    TransportInfo('web', 'src', 'dest'))
                self.survey_response_service.save_survey_response(request)
                self.fail('Since the form model is inactive it should raise an exception')
            except InactiveFormModelException:
                pass
            calls = [call(self.dbm, 'some_form_code')]
            patched_form_model.assert_has_calls(calls)


class TestSurveyResponseServiceIT(MangroveTestCase):
    def test_survey_response_is_saved(self):
        test_data = TestData(self.manager)
        survey_response_service = SurveyResponseService(self.manager)

        request = Request({'form_code': 'CL1', 'ID': test_data.entity1.short_code, 'Q1': 'name', 'Q2': '80', 'Q3': 'a'},
            TransportInfo('web', 'src', 'dest'))
        response = survey_response_service.save_survey_response(request)

        self.assertTrue(response.success)
        self.assertEqual(0, response.errors.__len__())
        self.assertIsNotNone(response.datarecord_id)
        self.assertIsNotNone(response.submission_id)
        self.assertEqual(test_data.entity_type, response.entity_type)
        self.assertEqual('CL1', response.form_code)
        self.assertEqual('1', response.short_code)
        self.assertDictEqual(OrderedDict([('Q1', 'name'), ('Q3', ['RED']), ('Q2', 80), ('ID', u'1')]),
            response.processed_data)

        submission = Submission.get(self.manager, response.submission_id)
        self.assertDictEqual({'Q1': 'name', 'Q3': 'a', 'Q2': '80', 'ID': '1'}, submission.values)
        self.assertDictEqual({'Q1': 'name', 'Q3': 'a', 'Q2': '80', 'ID': '1'}, submission.values)
        pass