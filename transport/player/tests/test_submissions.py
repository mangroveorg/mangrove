# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager, get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, NumberNotRegisteredException
from mangrove.transport.player.player import SMSPlayer, WebPlayer
from mangrove.transport.submissions import Request, SubmissionHandler, UnknownTransportException


class TestSubmissions(TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')

        self.form_model_patcher = patch('mangrove.transport.submissions.form_model')
        self.entity_patcher = patch('mangrove.transport.submissions.entity')
        self.reporter_patcher = patch('mangrove.transport.submissions.reporter')
        self.form_model_module = self.form_model_patcher.start()
        self.entity_module = self.entity_patcher.start()
        self.reporter_module = self.reporter_patcher.start()
        self.reporter_module.find_reporter.return_value = [{"first_name": "1234"}]

    def tearDown(self):
        self.form_model_patcher.stop()
        self.entity_patcher.stop()
        self.reporter_patcher.stop()

        _delete_db_and_remove_db_manager(self.dbm)

    def test_should_log_submission(self):
        request = Request(transport="sms", message="QR1 +EID 100 +Q1 20", source="1234", destination="5678")
        # dbm = Mock(spec=DatabaseManager)
        dbm = self.dbm
        s = SubmissionHandler(dbm)
        self.form_model_module.get_form_model_by_code.side_effect = FormModelDoesNotExistsException("hello")
        response = s.accept(request)
        submission_log = dbm._load_document(response.submission_id, SubmissionLogDocument)
        # submission_log = dbm.save.call_args_list[0][0][0]
        self.assertIsInstance(submission_log, SubmissionLogDocument)
        self.assertEquals(request.transport, submission_log.channel)
        self.assertEquals(request.source, submission_log.source)
        self.assertEquals(request.destination, submission_log.destination)
        self.assertEquals(False, submission_log. status)
        self.assertEquals("QR1", submission_log.form_code)
        self.assertEquals({'q1': '20', 'eid': '100'}, submission_log.values)
        self.assertEquals(request.destination, submission_log.destination)

    def test_should_check_if_submission_by_registered_reporter(self):
        request = Request(transport="sms", message="hello world", source="1234", destination="5678")
        # dbm = Mock(spec=DatabaseManager)
        dbm = self.dbm
        form = Mock()
        form.type = "survey"
        self.form_model_module.get_form_model_by_code.return_value = form
        self.reporter_module.find_reporter.side_effect = NumberNotRegisteredException("1234")
        s = SubmissionHandler(dbm)
        response = s.accept(request)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("Sorry, this number 1234 is not registered with us.", response.errors[0])

    def test_should_fail_submission_if_invalid_form_code(self):
        request = Request(transport="sms", message="INVALID_CODE +name xyz +age 10",
                          source="1234", destination="5678")
        dbm = Mock(spec=DatabaseManager)
        self.form_model_module.get_form_model_by_code.side_effect = FormModelDoesNotExistsException("INVALID_CODE")
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
        with self.assertRaises(UnknownTransportException) :
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
