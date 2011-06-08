# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.errors.MangroveException import  NumberNotRegisteredException
from mangrove.form_model.form_model import  NAME_FIELD
from mangrove.transport.player.player import SMSPlayer, Request
from mangrove.transport.submissions import SubmissionHandler


class TestSMSPlayer(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.submission_handler_mock = Mock(spec=SubmissionHandler)
        self.reporter_patcher = patch('mangrove.transport.player.player.reporter')
        self.reporter_module = self.reporter_patcher.start()
        self.reporter_module.find_reporter.return_value = [{NAME_FIELD: "1234"}]

    def tearDown(self):
        self.reporter_patcher.stop()

    def test_should_check_if_submission_by_registered_reporter(self):
        with self.assertRaises(NumberNotRegisteredException):
            request = Request(transport="sms", message="hello world", source="1234", destination="5678")
            self.reporter_module.find_reporter.side_effect = NumberNotRegisteredException("1234")

            player = SMSPlayer(self.dbm, self.submission_handler_mock)
            player.accept(request)

