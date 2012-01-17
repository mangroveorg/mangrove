import unittest
from mock import Mock
from mangrove.form_model.form_model import FormModel
from mangrove.errors.MangroveException import SMSParserInvalidFormatException, SMSParserWrongNumberOfAnswersException
from mangrove.transport.player.parser import OrderSMSParser

class TestOrderSMSParser(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock()
        self.sms_parser = OrderSMSParser(self.dbm)

    def _mock_get_question_codes_from_couchdb(self, question_code,is_registration_form=True):
        self.sms_parser._get_question_codes = Mock()
        form_model = Mock(spec=FormModel)
        form_model.is_registration_form.return_value=is_registration_form
        self.sms_parser._get_question_codes.return_value = question_code,form_model

    def test_should_return_all_answers(self):
        message = "questionnaire_code q1_answer q2_answer q3_answer"
        self._mock_get_question_codes_from_couchdb(['q1', 'q2', 'q3'])

        values = self.sms_parser.parse(message)
        question_code_and_answers = {"q1": "q1_answer", "q2": "q2_answer", "q3": "q3_answer"}
        expected = ("questionnaire_code", question_code_and_answers)

        self.assertEqual(expected, values)

    def test_should_accept_only_strings(self):
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(10)
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(None)

    def test_num_of_answers_not_the_same_as_num_of_questions_for_submission(self):
        message = "questionnaire_code q1_answer q2_answer"
        is_registration_form = False
        self._mock_get_question_codes_from_couchdb(['q1', 'q2', 'q3'], is_registration_form)
        with self.assertRaises(SMSParserWrongNumberOfAnswersException): self.sms_parser.parse(message)

        self._mock_get_question_codes_from_couchdb(['q1'],is_registration_form)
        with self.assertRaises(SMSParserWrongNumberOfAnswersException): self.sms_parser.parse(message)

    def test_invalid_format_message(self):
        message = "questionnaire_code .q1 q1_answer .q2 q2_answer .q3 q3_answer"
        self._mock_get_question_codes_from_couchdb(['q1', 'q2', 'q3'])
        with self.assertRaises(SMSParserInvalidFormatException): self.sms_parser.parse(message)

    def test_should_ignore_additional_space_separators(self):
        message = "questionnaire_code q1_answer q2_answer                   q3_answer"
        self._mock_get_question_codes_from_couchdb(['q1', 'q2', 'q3'])

        values = self.sms_parser.parse(message)
        question_code_and_answers = {"q1": "q1_answer", "q2": "q2_answer", "q3": "q3_answer"}
        expected = ("questionnaire_code", question_code_and_answers)

        self.assertEqual(expected, values)

