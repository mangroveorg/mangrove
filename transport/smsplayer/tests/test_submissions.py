# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.transport.submissions import Request, SubmissionHandler, Response


class TestSubmissions(TestCase):
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

#test_get_player
#test_authorize


