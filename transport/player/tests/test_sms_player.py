# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase, SkipTest
from mock import Mock, patch
from datawinners import settings
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.errors.MangroveException import  NumberNotRegisteredException, SMSParserInvalidFormatException, MultipleSubmissionsForSameCodeException
from mangrove.form_model.form_model import FormModel
from mangrove.transport.player.parser import KeyBasedSMSParser, OrderSMSParser
from mangrove.transport.player.player import SMSPlayer, Request, TransportInfo


class TestSMSPlayer(TestCase):
    def _mock_reporter(self):
        self.reporter_mock = Mock(spec=Entity)
        reporter_name = "1234"
        self.reporter_module.find_reporter_entity.return_value = self.reporter_mock

    def setUp(self):
        self.loc_tree = Mock()
        self.loc_tree.get_hierarchy_path.return_value = None
        self.dbm = Mock(spec=DatabaseManager)
        self._mock_form_model()
        self.reporter_patcher = patch('mangrove.transport.player.player.reporter')
        self.reporter_module = self.reporter_patcher.start()
        self._mock_reporter()
        self.transport = TransportInfo(transport="sms", source="1234", destination="5678")
        self.message = "FORM_CODE .ID 1 .M hello world"
        self.sms_player = SMSPlayer(self.dbm, self.loc_tree)
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
        form_code, values = KeyBasedSMSParser().parse(self.message)
        self.sms_player.accept(self.transport, form_code, values)

        self.assertEqual(1, self.form_model_mock.submit.call_count)

    #    TODO: Rewrite below test, skipping for now
    @SkipTest
    def test_should_submit_if_submission_by_registered_reporter(self):
        form_code, values = KeyBasedSMSParser().parse(self.message)
        self.sms_player.accept(self.transport, form_code, values)

        self.assertEqual(1, self.form_model_mock.submit.call_count)

        submission_request = self.form_model_mock.submit.call_args[0][0]
        self.assertEqual(self.reporter_mock, submission_request.reporter)

    def test_should_check_if_submission_by_unregistered_reporter(self):
        self.reporter_module.find_reporter_entity.side_effect = NumberNotRegisteredException("1234")
        with self.assertRaises(NumberNotRegisteredException):
            form_code, values = KeyBasedSMSParser().parse(self.message)
            self.sms_player.accept(self.transport, form_code, values)


    def test_should_not_submit_if_parsing_is_not_successful(self):
        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = KeyBasedSMSParser().parse("invalid format")
            self.sms_player.accept(self.transport, form_code, values)

        self.assertEqual(0, self.form_model_mock.submit.call_count)


    def test_should_not_parse_if_two_question_codes(self):
        transport = TransportInfo(transport="sms", source="1234", destination="5678")
        with self.assertRaises(MultipleSubmissionsForSameCodeException):
            form_code, values = KeyBasedSMSParser().parse("cli001 .na tester1 .na tester2")
            self.sms_player.accept(transport, form_code, values)

        self.assertEqual(0, self.form_model_mock.submit.call_count)

    def test_should_accept_ordered_sms_message(self):
        self.request = Request(transportInfo=self.transport,
                               message="questionnaire_code question1_answer question2_answer")
        order_sms_parser = OrderSMSParser(self.dbm)
        order_sms_parser._get_question_codes_from_couchdb = Mock()
        order_sms_parser._get_question_codes_from_couchdb.return_value = ['q1', 'q2']
        form_code, values = order_sms_parser.parse("questionnaire_code question1_answer question2_answer")
        SMSPlayer(self.dbm, self.loc_tree, order_sms_parser).accept(self.transport, form_code, values)
        self.assertEqual(1, self.form_model_mock.submit.call_count)


