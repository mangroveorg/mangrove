import unittest
from django.utils.unittest.case import SkipTest
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.form_model import FormModel
from mangrove.errors.MangroveException import SMSParserInvalidFormatException, SMSParserWrongNumberOfAnswersException
from mangrove.transport.player.parser import OrderSMSParser, SMSParser
@SkipTest
class TestOrderSMSParser(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.sms_parser = OrderSMSParser(self.dbm)

    def _mock_get_question_codes_from_couchdb(self, question_code,is_registration_form=True):
        self.sms_parser._get_question_codes = Mock()
        form_model = Mock(spec=FormModel)
        form_model.is_entity_registration_form.return_value=is_registration_form
        self.get_question_codes_patch = patch.object(SMSParser, "get_question_codes")
        self.get_question_codes_mock = self.get_question_codes_patch.start()
        self.get_question_codes_mock.return_value = question_code, form_model

    def test_should_return_all_answers(self):
        message = "questionnaire_code q1_answer q2_answer q3_answer"
        self._mock_get_question_codes_from_couchdb(['q1', 'q2', 'q3'])

        values = self.sms_parser.parse(message)
        question_code_and_answers = {"q1": "q1_answer", "q2": "q2_answer", "q3": "q3_answer"}
        expected = ("questionnaire_code", question_code_and_answers, [])

        self.assertEqual(expected, values)
        self.get_question_codes_patch.stop()

    def test_should_return_extra_data_with_answers(self):
        message = "questionnaire_code q1_answer q2_answer q3_answer extra1 extra2 extra3"
        self._mock_get_question_codes_from_couchdb(['q1', 'q2', 'q3'])

        values = self.sms_parser.parse(message)
        question_code_and_answers = {"q1": "q1_answer", "q2": "q2_answer", "q3": "q3_answer"}
        extra_data = ["extra1", "extra2", "extra3"]
        expected = ("questionnaire_code", question_code_and_answers, extra_data)

        self.assertEqual(expected, values)
        self.get_question_codes_patch.stop()
        
    def test_should_accept_only_strings(self):
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(10)
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(None)

    def test_should_ignore_additional_space_separators(self):
        message = "questionnaire_code q1_answer q2_answer                   q3_answer"
        self._mock_get_question_codes_from_couchdb(['q1', 'q2', 'q3'])

        values = self.sms_parser.parse(message)
        question_code_and_answers = {"q1": "q1_answer", "q2": "q2_answer", "q3": "q3_answer"}
        expected = ("questionnaire_code", question_code_and_answers, [])

        self.assertEqual(expected, values)
        self.get_question_codes_patch.stop()

