# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from unittest import TestCase
from mangrove.errors.MangroveException import SubmissionParseException, SMSParserInvalidFormatException
from mangrove.transport.player.parser import SMSParser
from nose.tools import nottest
from simplejson import OrderedDict
from datawinners import settings


class TestSMSParser(TestCase):
    def setUp(self):
        self.sms_parser = SMSParser()
        settings.USE_ORDERED_SMS_PARSER = False

    def test_should_return_all_answers_in_lower_case(self):
        message = "QUESTIONNAIRE_CODE id_1 FirstName age_10"
        settings.USE_ORDERED_SMS_PARSER = True
        values = self.sms_parser.parse(message)
        field_ids_and_answers = {"q1": "id_1", "q2": "FirstName", "q3" : "age_10"}
        expected = ("questionnaire_code", field_ids_and_answers)
        self.assertEqual(expected, values)

    def test_should_accept_only_strings_parsing_without_field(self):
        settings.USE_ORDERED_SMS_PARSER = True
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(10)
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(None)

    def test_should_return_form_code(self):
        tokens = ["QUESTIONNAIRE_CODE", "id_1", "FirstName"]
        form_code = self.sms_parser._pop_form_code(tokens)
        self.assertEqual("questionnaire_code", form_code)

    def test_should_return_answers_when_parsing_tokens_without_field_id(self):
        tokens = ["id_1", "FirstName", "age_10"]
        answers = self.sms_parser._parse_tokens_without_field_id(tokens)
        expected_answers = OrderedDict()
        expected_answers['q1'] = "id_1"
        expected_answers['q2'] = "FirstName"
        expected_answers['q3'] = "age_10"
        self.assertEqual(expected_answers, answers)

    def test_should_return_all_field_codes_in_lower_case(self):
        form_code, values = self.sms_parser.parse("WP .id 1 .Name FirstName .aGe 10")
        self.assertEqual({"id": "1", "name": "FirstName", "age": "10"}, values)

    def test_should_preserve_non_leading_white_spaces_in_answer(self):
        form_code, values = self.sms_parser.parse("WP .ID 1 .NAME FirstName LastName .AGE 10")
        self.assertEqual({"id": "1", "name": "FirstName LastName", "age": "10"}, values)

    def test_should_parse_incomplete_messages_with_no_answer_values(self):
        form_code, values = self.sms_parser.parse("WP .ID 1 .BC ")
        self.assertEqual({"id": "1", "bc": ""}, values)

    def test_should_raise_error_if_invalid_sms_format(self):
        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = self.sms_parser.parse("+")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = self.sms_parser.parse("  +  ")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = self.sms_parser.parse("  +  +")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = self.sms_parser.parse("+WP ")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = self.sms_parser.parse("WP")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = self.sms_parser.parse("WP+")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = self.sms_parser.parse(" WP ")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = self.sms_parser.parse("WP ID")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = self.sms_parser.parse("WP +ID")

    def test_should_accept_only_strings(self):
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(10)
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(None)

    def test_should_accept_unicode(self):
        form_code, values = self.sms_parser.parse(u"reg .s Āgra .n شصلكقم .m 080 .t clinic")
        self.assertEqual({u"s": u"Āgra", u"n": u"شصلكقم", u"m": u"080", u"t": u"clinic"}, values)


    def test_should_convert_input_to_unicode(self):
        form_code, values = self.sms_parser.parse("reg .s Āgra .n شصلكقم .m 080 .t clinic")
        self.assertEqual({u"s": u"Āgra", u"n": u"شصلكقم", u"m": u"080", u"t": u"clinic"}, values)


    def test_should_ignore_additional_separators(self):
        form_code, values = self.sms_parser.parse("WP .ID 1 . .. .NAME FirstName LastName .. .AGE 10 .. ")
        self.assertEqual({"id": "1", "name": "FirstName LastName", "age": "10"}, values)
        self.assertEqual("wp", form_code)

    def test_should_handle_gps(self):
        form_code, values = self.sms_parser.parse("WP .ID 1 .NAME FirstName.LastName .AGE 10")
        self.assertEqual({"id": "1", "name": "FirstName.LastName", "age": "10"}, values)

    def test_should_add_question_code_when_using_order_sms(self):
        settings.USE_ORDERED_SMS_PARSER = True
        question_code = ['uid', 'ag', 'qa']
        form_code, values = self.sms_parser.parse_ordered("WP 1 10 A", question_code)
        self.assertEqual({"uid": "1", "ag": "10", "qa": "A"}, values)
        self.assertEqual("wp", form_code)
        settings.USE_ORDERED_SMS_PARSER = False;

