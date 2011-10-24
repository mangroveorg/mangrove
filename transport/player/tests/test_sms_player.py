# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase, SkipTest
from mock import Mock, patch
from datawinners import settings
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.errors.MangroveException import  NumberNotRegisteredException, SMSParserInvalidFormatException, MultipleSubmissionsForSameCodeException
from mangrove.form_model.form_model import FormModel
from mangrove.transport.player.player import SMSPlayer, Request, TransportInfo

def _mock_get_question_codes_from_couchdb(dbm, form_code):
    return ["ID", "M"]

class TestSMSPlayer(TestCase):
    def _mock_reporter(self):
        self.reporter_mock = Mock(spec=Entity)
        reporter_name = "1234"
        self.reporter_module.find_reporter_entity.return_value = self.reporter_mock

    def setUp(self):
        loc_tree = Mock()
        loc_tree.get_hierarchy_path.return_value = None
        self.dbm = Mock(spec=DatabaseManager)
        self._mock_form_model()
        self.reporter_patcher = patch('mangrove.transport.player.player.reporter')
        self.reporter_module = self.reporter_patcher.start()
        self._mock_reporter()
        self.transport = TransportInfo(transport="sms", source="1234", destination="5678")
        self.request = Request(transportInfo=self.transport, message="FORM_CODE .ID 1 .M hello world")
        self.sms_player = SMSPlayer(self.dbm, loc_tree)
        self.generate_code_patcher = patch(
            "mangrove.transport.player.player.Player._update_submission_with_short_code_if_registration_form")
        self.generate_code_patcher.start()

    def _mock_form_model(self):
        self.get_form_model_mock_patcher = patch('mangrove.transport.player.player.get_form_model_by_code')
        get_form_model_mock = self.get_form_model_mock_patcher.start()
        self.form_model_mock = Mock(spec=FormModel)
        get_form_model_mock.return_value = self.form_model_mock

    def tearDown(self):
        self.reporter_patcher.stop()
        self.generate_code_patcher.stop()

    def test_should_submit_if_parsing_is_successful(self):
        self.sms_player.accept(self.request)

        self.assertEqual(1, self.form_model_mock.submit.call_count)

    #    TODO: Rewrite below test, skipping for now
    @SkipTest
    def test_should_submit_if_submission_by_registered_reporter(self):
        self.sms_player.accept(self.request)

        self.assertEqual(1, self.form_model_mock.submit.call_count)

        submission_request = self.form_model_mock.submit.call_args[0][0]
        self.assertEqual(self.reporter_mock, submission_request.reporter)

    def test_should_check_if_submission_by_unregistered_reporter(self):
        self.reporter_module.find_reporter_entity.side_effect = NumberNotRegisteredException("1234")
        with self.assertRaises(NumberNotRegisteredException):
            self.sms_player.accept(self.request)


    def test_should_not_submit_if_parsing_is_not_successful(self):
        self.request = Request(transportInfo=self.transport, message="invalid format")
        with self.assertRaises(SMSParserInvalidFormatException):
            self.sms_player.accept(self.request)

        self.assertEqual(0, self.form_model_mock.submit.call_count)


    def test_should_not_parse_if_two_question_codes(self):
        settings.USE_ORDERED_SMS_PARSER = False
        transport = TransportInfo(transport="sms", source="1234", destination="5678")
        self.request = Request(transportInfo=transport, message="cli001 .na tester1 .na tester2")
        with self.assertRaises(MultipleSubmissionsForSameCodeException):
            self.sms_player.accept(self.request)

        self.assertEqual(0, self.form_model_mock.submit.call_count)
        settings.USE_ORDERED_SMS_PARSER = False

    def test_should_accept_ordered_sms_message(self):
        settings.USE_ORDERED_SMS_PARSER = True
        self.request = Request(transportInfo=self.transport, message="FORM_CODE 1 hello")
        self.sms_player.accept(self.request, _mock_get_question_codes_from_couchdb)
        self.assertEqual(1, self.form_model_mock.submit.call_count)
        settings.USE_ORDERED_SMS_PARSER = False


