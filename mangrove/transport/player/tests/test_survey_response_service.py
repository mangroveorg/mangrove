from collections import OrderedDict
from datetime import datetime
from unittest import TestCase
from mock import Mock, patch, call
from mangrove.datastore.documents import SurveyResponseDocument
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.datastore.entity import DataRecord
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

    def test_create_submission_log_when_form_code_is_non_existent(self):
        SubmissionLogDocument.__eq__ = assert_submission_log_is('nonexistant_form_code')
        SurveyResponseDocument.__eq__ = assert_survey_response_doc_is('nonexistant_form_code')

        with patch.object(self.dbm, '_save_document') as save_document:
            with patch('mangrove.transport.services.survey_response_service.get_form_model_by_code') as get_form_model:
                get_form_model.side_effect = FormModelDoesNotExistsException('nonexistant_form_code')
                transport_info = TransportInfo('web', 'src', 'dest')
                values = {'form_code': 'nonexistant_form_code', 'q1': 'a1', 'q2': 'a2'}
                try:
                    request = Request(values, transport_info)
                    self.survey_response_service.save_survey('nonexistant_form_code', values, [], transport_info,
                        request.message)
                    self.fail('Expected FormModelDoesNotExistsException')
                except FormModelDoesNotExistsException:
                    pass
                get_form_model.assert_has_calls([call(self.dbm, 'nonexistant_form_code')])
                save_document.assert_has_calls([call(SubmissionLogDocument())])


    def test_create_submission_for_a_survey_response_for_inactive_form_code(self):
        form_model = Mock(spec=FormModel)
        with patch('mangrove.transport.services.survey_response_service.get_form_model_by_code') as patched_form_model:
            patched_form_model.return_value = form_model
            form_model.is_inactive.return_value = True
            self.dbm._save_document.return_value = SubmissionLogDocument()

            try:
                values = {'form_code': 'some_form_code', 'q1': 'a1', 'q2': 'a2'}
                transport_info = TransportInfo('web', 'src', 'dest')
                request = Request(values, transport_info)

                self.survey_response_service.save_survey('some_form_code', values, [], transport_info, request.message)
                self.fail('Since the form model is inactive it should raise an exception')
            except InactiveFormModelException:
                pass
            calls = [call(self.dbm, 'some_form_code')]
            patched_form_model.assert_has_calls(calls)

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

    def test_survey_response_is_edited_and_new_submission_and_datarecord_are_created(self):
        test_data = TestData(self.manager)
        survey_response_service = SurveyResponseService(self.manager)

        values = {'ID': test_data.entity1.short_code, 'Q1': 'name', 'Q2': '80', 'Q3': 'a'}
        transport_info = TransportInfo('web', 'src', 'dest')
        request = Request(values, transport_info)

        saved_response = survey_response_service.save_survey('CL1', values, [], transport_info, request.message)
        self.assertDictEqual(OrderedDict([('Q1', 'name'), ('Q3', ['RED']), ('Q2', 80), ('ID', u'1')]),
            saved_response.processed_data)

        new_values = {'ID': test_data.entity1.short_code, 'Q1': 'new_name', 'Q2': '430', 'Q3': 'b'}
        survey_response_to_edit = SurveyResponse.get(self.manager,saved_response.survey_response_id)
        edit_response = survey_response_service.edit_survey('CL1', new_values, [], transport_info,request.message,survey_response_to_edit)

        self.assertTrue(edit_response.success)
        self.assertEqual(0, edit_response.errors.__len__())
        self.assertIsNotNone(edit_response.datarecord_id)
        self.assertIsNotNone(edit_response.survey_response_id)
        self.assertEqual(test_data.entity_type, edit_response.entity_type)
        self.assertEqual('CL1', edit_response.form_code)
        self.assertEqual('1', edit_response.short_code)
        self.assertDictEqual(OrderedDict([('Q1', 'new_name'), ('Q3', ['YELLOW']), ('Q2', 430), ('ID', u'1')]),
            edit_response.processed_data)

        submission = Submission.get(self.manager, edit_response.submission_id)
        self.assertNotEquals(saved_response.submission_id, edit_response.submission_id)
        self.assertIsNotNone(submission.form_model_revision)
        self.assertDictEqual({'Q1': 'new_name', 'Q3': 'b', 'Q2': '430', 'ID': '1'}, submission.values)

        self.assertNotEquals(saved_response.datarecord_id,edit_response.datarecord_id)

        old_data_record = DataRecord.get(self.manager,saved_response.datarecord_id)
        self.assertTrue(old_data_record.voided)
        new_data_record = DataRecord.get(self.manager, edit_response.datarecord_id)
        self.assertFalse(new_data_record.voided)
