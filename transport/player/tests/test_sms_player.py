# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.errors.MangroveException import  NumberNotRegisteredException, SMSParserInvalidFormatException, MultipleSubmissionsForSameCodeException
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
        self.request = Request(transport="sms", message="FORM_CODE +ID 1 +M hello world", source="1234", destination="5678")
        self.sms_player = SMSPlayer(self.dbm, self.submission_handler_mock)

    def tearDown(self):
        self.reporter_patcher.stop()

    def test_should_submit_if_parsing_is_successful(self):
        self.sms_player.accept(self.request)

        self.assertEqual(1,self.submission_handler_mock.accept.call_count)

    def test_should_not_submit_if_parsing_is_not_successful(self):
        self.request = Request(transport="sms", message="invalid format", source="1234", destination="5678")
        with self.assertRaises(SMSParserInvalidFormatException):
            self.sms_player.accept(self.request)

        self.assertEqual(0,self.submission_handler_mock.accept.call_count)

    def test_should_check_if_submission_by_registered_reporter(self):
        self.reporter_module.find_reporter.side_effect = NumberNotRegisteredException("1234")
        with self.assertRaises(NumberNotRegisteredException):
            self.sms_player.accept(self.request)

    def test_should_not_parse_if_two_question_codes(self):
        self.request = Request(transport="sms", message="cli001 +na tester1 +na tester2", source="1234", destination="5678")
        with self.assertRaises(MultipleSubmissionsForSameCodeException):
            self.sms_player.accept(self.request)

        self.assertEqual(0,self.submission_handler_mock.accept.call_count)