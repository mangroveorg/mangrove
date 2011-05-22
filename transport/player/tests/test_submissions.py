# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager, get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, NumberNotRegisteredException
from mangrove.form_model.form_model import FormModel, FormSubmission
from mangrove.transport.player.player import SMSPlayer, WebPlayer
from mangrove.transport.submissions import Request, SubmissionHandler, UnknownTransportException, SubmissionLogger


class TestSubmissions(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.form_model_patcher = patch('mangrove.transport.submissions.get_form_model_by_code')
        self.entity_patcher = patch('mangrove.transport.submissions.entity')
        self.reporter_patcher = patch('mangrove.transport.submissions.reporter')
        self.SubmissionLogger_class_patcher = patch('mangrove.transport.submissions.SubmissionLogger',)

        self.get_form_model_mock = self.form_model_patcher.start()
        self.entity_module = self.entity_patcher.start()
        self.reporter_module = self.reporter_patcher.start()
        self.SubmissionLogger_mock_class = self.SubmissionLogger_class_patcher.start()
        self.submissionLogger = Mock(spec=SubmissionLogger)
        self.SubmissionLogger_mock_class.return_value = self.submissionLogger
        self.SUBMISSION_ID = "SUBMISSION_ID"
        self.submissionLogger.create_submission_log.return_value = self.SUBMISSION_ID

        self.reporter_module.find_reporter.return_value = [{"first_name": "1234"}]
        self.form_model_mock = Mock(spec=FormModel)
        self.get_form_model_mock.return_value = self.form_model_mock

    def tearDown(self):
        self.form_model_patcher.stop()
        self.entity_patcher.stop()
        self.reporter_patcher.stop()

    def _valid_form_submission(self):
        return FormSubmission(self.form_model_mock, {}, "1", True, {})

    def _invalid_form_submission(self):
        return FormSubmission(self.form_model_mock, {}, "1", False, {"field" :"Invalid"})

    def test_should_return_true_if_valid_form_submission(self):
        self.form_model_mock.validate_submission.return_value = self._valid_form_submission()

        request = Request(transport="sms", message="QR1 +EID 100 +Q1 20", source="1234", destination="5678")
        s = SubmissionHandler(self.dbm)
        response = s.accept(request)

        self.assertTrue(response.success)

    def test_should_save_data_record_if_valid_form_submission(self):
        self.form_model_mock.validate_submission.return_value = self._valid_form_submission()

        request = Request(transport="sms", message="QR1 +EID 100 +Q1 20", source="1234", destination="5678")
        s = SubmissionHandler(self.dbm)
        response = s.accept(request)

        self.assertTrue(self.entity_module.add_data.called)


    def test_should_not_save_data_record_if_in_valid_form_submission(self):
        self.form_model_mock.validate_submission.return_value = self._invalid_form_submission()

        request = Request(transport="sms", message="QR1 +EID 100 +Q1 20", source="1234", destination="5678")
        s = SubmissionHandler(self.dbm)
        response = s.accept(request)

        self.assertFalse(self.entity_module.add_data.called)
        self.assertFalse(response.success)


    def test_should_create_new_submission_log(self):

        request = Request(transport="sms", message="QR1 +EID 100 +Q1 20", source="1234", destination="5678")
        s = SubmissionHandler(self.dbm)
        response = s.accept(request)

        self.submissionLogger.create_submission_log.assert_called_once_with(channel = "sms",
                                                                            source = "1234",
                                                                            destination = "5678",
                                                                            form_code = "QR1",
                                                                            values = { "eid" : "100", "q1" : "20" }
        )


    def test_should_update_submission_log_on_success(self):
        form_submission = self._valid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission

        request = Request(transport="sms", message="QR1 +EID 100 +Q1 20", source="1234", destination="5678")
        s = SubmissionHandler(self.dbm)
        response = s.accept(request)

        self.submissionLogger.update_submission_log.assert_called_once_with(submission_id = self.SUBMISSION_ID,status = True, errors = [])


    def test_should_update_submission_log_on_failure(self):
        form_submission = self._invalid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission

        request = Request(transport="sms", message="QR1 +EID 100 +Q1 20", source="1234", destination="5678")
        s = SubmissionHandler(self.dbm)
        response = s.accept(request)

        self.submissionLogger.update_submission_log.assert_called_once_with(submission_id = self.SUBMISSION_ID,
                                                                            status = False,
                                                                            errors = form_submission.errors.values())


    def test_should_check_if_submission_by_registered_reporter(self):
        request = Request(transport="sms", message="hello world", source="1234", destination="5678")
        # dbm = Mock(spec=DatabaseManager)
        dbm = self.dbm
        form = Mock()
        form.type = "survey"
        self.get_form_model_mock.return_value = form
        self.reporter_module.find_reporter.side_effect = NumberNotRegisteredException("1234")
        s = SubmissionHandler(dbm)
        response = s.accept(request)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("Sorry, this number 1234 is not registered with us.", response.errors[0])

    def test_should_fail_submission_if_invalid_form_code(self):
        request = Request(transport="sms", message="INVALID_CODE +name xyz +age 10",
                          source="1234", destination="5678")
        dbm = Mock(spec=DatabaseManager)
        self.get_form_model_mock.side_effect = FormModelDoesNotExistsException("INVALID_CODE")
        s = SubmissionHandler(dbm)
        response = s.accept(request)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("The questionnaire with code INVALID_CODE does not exist.", response.errors[0])
        self.assertEqual("The questionnaire with code INVALID_CODE does not exist.", response.message)

    def test_should_return_SMSPlayer_for_sms_transport(self):
        request = Request(transport='sms', message='blah', source='rep1', destination='HNI')
        mock_dbm = Mock(spec=DatabaseManager)
        sub_handler = SubmissionHandler(dbm=mock_dbm)
        self.assertIsInstance(sub_handler.get_player_for_transport(request), SMSPlayer)

    def test_should_return_WebPlayer_for_web_transport(self):
        request = Request(transport='web', message='blah', source='rep1', destination='HNI')
        mock_dbm = Mock(spec=DatabaseManager)
        sub_handler = SubmissionHandler(dbm=mock_dbm)
        self.assertIsInstance(sub_handler.get_player_for_transport(request), WebPlayer)
    
    def test_should_return_UnknownTransportException_for_unknown_transport(self):
        with self.assertRaises(UnknownTransportException):
            request = Request(transport='garbage', message='blah', source='rep1', destination='HNI')
            mock_dbm = Mock(spec=DatabaseManager)
            sub_handler = SubmissionHandler(dbm=mock_dbm)
            sub_handler.get_player_for_transport(request)

#TODO : need to rewrite this test when Submission handler is broken in two part
#    def test_should_return_success_message_with_reporter_name(self):
#        request = Request(transport="sms", message="hello world", source="1234", destination="5678")
#        dbm = Mock(spec=DatabaseManager)
#        self.reporter_module.find_reporter.return_value = [
#                    {"first_name": "Reporter A", "telephone_number": "1234"},
#                    ]
#        s = SubmissionHandler(dbm)
#        response = s.accept(request)
#        self.assertEqual("Thank You Reporter A for your submission.", response.message)
#test_get_player
#test_authorize
