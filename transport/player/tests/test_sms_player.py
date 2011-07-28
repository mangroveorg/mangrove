# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.errors.MangroveException import  NumberNotRegisteredException, SubmissionParseException
from mangrove.transport.player.player import SMSPlayer, Request, TransportInfo
from mangrove.transport.submissions import SubmissionHandler


class TestSMSPlayer(TestCase):
    def _mock_reporter(self):
        self.reporter_mock = Mock(spec=Entity)
        reporter_name = "1234"
        self.reporter_module.find_reporter_entity.return_value = self.reporter_mock, reporter_name

    def setUp(self):
        loc_tree = Mock()
        loc_tree.get_hierarchy_path.return_value = None
        self.dbm = Mock(spec=DatabaseManager)
        self.submission_handler_mock = Mock(spec=SubmissionHandler)
        self.reporter_patcher = patch('mangrove.transport.player.player.reporter')
        self.reporter_module = self.reporter_patcher.start()
        self._mock_reporter()
        self.transport = TransportInfo(transport="sms", source="1234", destination="5678")
        self.request = Request( transportInfo=self.transport, message="FORM_CODE +ID 1 +M hello world")
        self.sms_player = SMSPlayer(self.dbm, self.submission_handler_mock, loc_tree)
        self.generate_code_patcher = patch("mangrove.transport.player.player.Player._handle_registration_form")
        self.generate_code_patcher.start()

    def tearDown(self):
        self.reporter_patcher.stop()
        self.generate_code_patcher.stop()

    def test_should_submit_if_parsing_is_successful(self):
        self.sms_player.accept(self.request)

        self.assertEqual(1, self.submission_handler_mock.accept.call_count)

    def test_should_submit_if_submission_by_registered_reporter(self):

        self.sms_player.accept(self.request)

        self.assertEqual(1, self.submission_handler_mock.accept.call_count)

        submission_request = self.submission_handler_mock.accept.call_args[0][0]
        self.assertEqual(self.reporter_mock, submission_request.reporter)

    def test_should_check_if_submission_by_unregistered_reporter(self):
        self.reporter_module.find_reporter_entity.side_effect = NumberNotRegisteredException("1234")
        with self.assertRaises(NumberNotRegisteredException):
            self.sms_player.accept(self.request)


    def test_should_not_submit_if_parsing_is_not_successful(self):
        self.request = Request(transportInfo=self.transport, message="invalid format")
        with self.assertRaises(SubmissionParseException):
            self.sms_player.accept(self.request)

        self.assertEqual(0, self.submission_handler_mock.accept.call_count)


    def test_should_not_parse_if_two_question_codes(self):
        transport = TransportInfo(transport="sms", source="1234", destination="5678")
        self.request = Request(transportInfo=transport, message="cli001 +na tester1 +na tester2")
        with self.assertRaises(SubmissionParseException):
            self.sms_player.accept(self.request)

        self.assertEqual(0, self.submission_handler_mock.accept.call_count)


