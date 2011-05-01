# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from _ast import Sub
from unittest.case import TestCase
from mock import Mock, patch
import mangrove
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.form_model.form_model import get_questionnaire
from mangrove.transport.submissions import Request, SubmissionHandler, Response


class TestSubmissions(TestCase):

    def setUp(self):
        self.form_model_patcher = patch('mangrove.transport.submissions.form_model')
        self.entity_patcher = patch('mangrove.transport.submissions.entity')
        self.reporter_patcher = patch('mangrove.transport.submissions.reporter')
        self.form_model_module = self.form_model_patcher.start()
        self.entity_module = self.entity_patcher.start()
        self.reporter_module = self.reporter_patcher.start()

    def tearDown(self):
        self.form_model_patcher.stop()
        self.entity_patcher.stop()
        self.reporter_patcher.stop()

    def test_should_accept_sms_submission(self):
        request = Request(transport = "sms", message = "hello world",source = "1234", destination = "5678")
        dbm = Mock(spec=DatabaseManager)
        s = SubmissionHandler(dbm)
        response = s.accept(request)
        self.assertIsNotNone(response)
        self.assertIsInstance(response,Response)
        self.assertIsNotNone(response.submission_id)
        self.assertIsNotNone(response.message)
        self.assertIsNotNone(response.success)

    def test_should_log_submission(self):
        request = Request(transport = "sms",message = "hello world",source = "1234", destination = "5678")
        dbm = Mock(spec=DatabaseManager)
        s = SubmissionHandler(dbm)
        s.accept(request)
        submission_log = dbm.save.call_args[0][0]
        self.assertIsInstance(submission_log,SubmissionLogDocument)
        self.assertEquals(request.transport,submission_log.channel)
        self.assertEquals(request.message,submission_log.message)
        self.assertEquals(request.source,submission_log.source)
        self.assertEquals(request.destination,submission_log.destination)

#            Incomplete test: FIX IT
    def test_should_check_if_submission_by_registered_reporter(self):
        request = Request(transport = "sms",message = "hello world",source = "1234", destination = "5678")
        dbm = Mock(spec=DatabaseManager)
        s = SubmissionHandler(dbm)
        s.accept(request)
        pass



#test_get_player
#test_authorize


