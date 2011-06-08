# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from unittest.case import TestCase
from mangrove.errors.MangroveException import SMSParserInvalidFormatException
from mangrove.transport.player.player import SMSParser, WebParser


class TestSMSParser(TestCase):

    def test_should_return_all_field_codes_in_lower_case(self):
        smsplayer = SMSParser()
        form_code, values = smsplayer.parse("WP +id 1 +Name FirstName +aGe 10")
        self.assertEqual({"id": "1", "name": "FirstName", "age": "10"}, values)

    def test_should_preserve_non_leading_white_spaces_in_answer(self):
        smsplayer = SMSParser()
        form_code, values = smsplayer.parse("WP +ID 1 +NAME FirstName LastName +AGE 10")
        self.assertEqual({"id": "1", "name": "FirstName LastName", "age": "10"}, values)

    def test_should_parse_incomplete_messages_with_no_answer_values(self):
        smsplayer = SMSParser()
        form_code, values = smsplayer.parse("WP +ID 1 +BC ")
        self.assertEqual({"id": "1", "bc": ""}, values)

    def test_should_raise_error_if_invalid_sms_format(self):
        smsplayer = SMSParser()
        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = smsplayer.parse("+")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = smsplayer.parse("  +  ")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = smsplayer.parse("  +  +")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = smsplayer.parse("+WP ")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = smsplayer.parse("WP")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = smsplayer.parse("WP+")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = smsplayer.parse(" WP ")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = smsplayer.parse("WP ID")

        with self.assertRaises(SMSParserInvalidFormatException):
            form_code, values = smsplayer.parse("WP +ID")

    def test_should_ignore_additional_separators(self):
        smsplayer = SMSParser()
        form_code, values = smsplayer.parse("WP +ID 1 + ++ +NAME FirstName LastName ++ +AGE 10 ++ ")
        self.assertEqual({"id": "1", "name": "FirstName LastName", "age": "10"}, values)
        self.assertEqual("WP", form_code)


    def test_should_return_form_code_and_message_as_dict(self):
        player = WebParser()
        message = {'form_code': 'X1', 'q1': 'a1', 'q2': 'a2'}
        form_code,values = player.parse(message)
        self.assertEquals(form_code, 'X1')
        self.assertEquals(values, {'q1': 'a1', 'q2': 'a2'})
