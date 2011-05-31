# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, NumberNotRegisteredException, NoQuestionsSubmittedException
from mangrove.form_model.form_model import FormModel, FormSubmission, NAME_FIELD
from mangrove.transport.player.player import SMSPlayer, WebPlayer
from mangrove.transport.submissions import Request, SubmissionHandler, UnknownTransportException, SubmissionLogger


class TestSubmissions(TestCase):

    ENTITY_TYPE = ["EntityType"]

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

        self.reporter_module.find_reporter.return_value = [{NAME_FIELD: "1234"}]
        self.form_model_mock = Mock(spec=FormModel)
        self.form_model_mock._is_registration_form.return_value = False
        self.get_form_model_mock.return_value = self.form_model_mock

    def tearDown(self):
        self.form_model_patcher.stop()
        self.entity_patcher.stop()
        self.reporter_patcher.stop()

    def _valid_form_submission(self):
        return FormSubmission(self.form_model_mock, {'What is associated entity?':'CID001', "location":"Pune"}, "1", True, {}, self.ENTITY_TYPE,data={})

    def _empty_form_submission(self):
        return FormSubmission(self.form_model_mock, {'What is associated entity?':'CID001'}, "1", True, {}, self.ENTITY_TYPE,data={})


    def _invalid_form_submission(self):
        return FormSubmission(self.form_model_mock, {}, "1", False, {"field" :"Invalid"}, self.ENTITY_TYPE, data={})

    def test_should_return_true_if_valid_form_submission(self):
        self.form_model_mock.validate_submission.return_value = self._valid_form_submission()

        request = Request(transport="sms", message="QR1 +EID 100 +Q1 20", source="1234", destination="5678")
        s = SubmissionHandler(self.dbm)
        response = s.accept(request)

        self.assertTrue(response.success)
        self.assertEqual({}, response.errors)


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
        self.assertEqual({"field" :"Invalid"}, response.errors)
        self.assertFalse(response.success)

    def test_should_not_save_data_record_if_no_valid_questions_present(self):
        self.form_model_mock.validate_submission.return_value = self._empty_form_submission()
        request = Request(transport="sms", message="QR1 +EID 100", source="1234", destination="5678")
        s = SubmissionHandler(self.dbm)
        with self.assertRaises(NoQuestionsSubmittedException):
            response = s.accept(request)

    def test_should_create_new_submission_log(self):
        form_submission = self._valid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission
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
        with self.assertRaises(NumberNotRegisteredException):
            request = Request(transport="sms", message="hello world", source="1234", destination="5678")
            dbm = self.dbm
            form = Mock()
            form.type = "survey"
            self.get_form_model_mock.return_value = form
            self.reporter_module.find_reporter.side_effect = NumberNotRegisteredException("1234")
            s = SubmissionHandler(dbm)
            s.accept(request)


    def test_should_fail_submission_if_invalid_form_code(self):
        with self.assertRaises(FormModelDoesNotExistsException):
            request = Request(transport="sms", message="INVALID_CODE +name xyz +age 10",
                              source="1234", destination="5678")
            dbm = Mock(spec=DatabaseManager)
            self.get_form_model_mock.side_effect = FormModelDoesNotExistsException("INVALID_CODE")
            s = SubmissionHandler(dbm)
            s.accept(request)
        
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

    def test_should_register_entity_if_form_submission_valid(self):
        self.form_model_mock.validate_submission.return_value = self._valid_form_submission()
        self.form_model_mock._is_registration_form.return_value = True

        request = Request(transport="sms", message="CODE +name xyz +age 10",
                          source="1234", destination="5678")
        handler = SubmissionHandler(self.dbm)
        response = handler.accept(request)
        self.assertTrue(response.success)
        self.assertEqual({}, response.errors)
        self.entity_module.create_entity.assert_called_once_with(dbm=self.dbm,entity_type=self.ENTITY_TYPE,
                                                                 location=["Pune"],
                                                                 aggregation_paths=None, short_code="1",geometry=None)
        self.submissionLogger.update_submission_log.assert_called_once_with(submission_id = self.SUBMISSION_ID,
                                                                            status = True, errors = [])


    def test_should_not_register_entity_if_form_submission_invalid(self):
        form_submission = self._invalid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission
        self.form_model_mock._is_registration_form.return_value = True

        request = Request(transport="sms", message="CODE +name xyz +age 10",
                          source="1234", destination="5678")
        handler = SubmissionHandler(self.dbm)
        response = handler.accept(request)
        self.assertFalse(response.success)
        self.assertEqual({"field" :"Invalid"}, response.errors)
        self.assertFalse(self.entity_module.create_entity.called)
        self.submissionLogger.update_submission_log.assert_called_once_with(submission_id = self.SUBMISSION_ID,
                                                                            status = False, errors = form_submission.errors.values() )


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
