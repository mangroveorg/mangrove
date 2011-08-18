# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from unittest import TestCase
from mangrove.errors.MangroveException import SubmissionParseException
from mangrove.transport.player.parser import SMSParser, WebParser


class TestSMSParser(TestCase):
    def setUp(self):
        self.sms_parser = SMSParser()

    def test_should_return_all_field_codes_in_lower_case(self):
        form_code, values = self.sms_parser.parse("WP +id 1 +Name FirstName +aGe 10")
        self.assertEqual({"id": "1", "name": "FirstName", "age": "10"}, values)

    def test_should_preserve_non_leading_white_spaces_in_answer(self):
        form_code, values = self.sms_parser.parse("WP +ID 1 +NAME FirstName LastName +AGE 10")
        self.assertEqual({"id": "1", "name": "FirstName LastName", "age": "10"}, values)

    def test_should_parse_incomplete_messages_with_no_answer_values(self):
        form_code, values = self.sms_parser.parse("WP +ID 1 +BC ")
        self.assertEqual({"id": "1", "bc": ""}, values)

    def test_should_raise_error_if_invalid_sms_format(self):
        with self.assertRaises(SubmissionParseException):
            form_code, values = self.sms_parser.parse("+")

        with self.assertRaises(SubmissionParseException):
            form_code, values = self.sms_parser.parse("  +  ")

        with self.assertRaises(SubmissionParseException):
            form_code, values = self.sms_parser.parse("  +  +")

        with self.assertRaises(SubmissionParseException):
            form_code, values = self.sms_parser.parse("+WP ")

        with self.assertRaises(SubmissionParseException):
            form_code, values = self.sms_parser.parse("WP")

        with self.assertRaises(SubmissionParseException):
            form_code, values = self.sms_parser.parse("WP+")

        with self.assertRaises(SubmissionParseException):
            form_code, values = self.sms_parser.parse(" WP ")

        with self.assertRaises(SubmissionParseException):
            form_code, values = self.sms_parser.parse("WP ID")

        with self.assertRaises(SubmissionParseException):
            form_code, values = self.sms_parser.parse("WP +ID")

    def test_should_accept_only_strings(self):
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(10)
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(None)


    def test_should_accept_unicode(self):
        form_code, values = self.sms_parser.parse(u"reg +s Āgra +n شصلكقم +m 080 +t clinic")
        self.assertEqual({u"s": u"Āgra", u"n": u"شصلكقم", u"m": u"080", u"t": u"clinic"}, values)


    def test_should_convert_input_to_unicode(self):
        form_code, values = self.sms_parser.parse("reg +s Āgra +n شصلكقم +m 080 +t clinic")
        self.assertEqual({u"s": u"Āgra", u"n": u"شصلكقم", u"m": u"080", u"t": u"clinic"}, values)


    def test_should_ignore_additional_separators(self):
        form_code, values = self.sms_parser.parse("WP +ID 1 + ++ +NAME FirstName LastName ++ +AGE 10 ++ ")
        self.assertEqual({"id": "1", "name": "FirstName LastName", "age": "10"}, values)
        self.assertEqual("wp", form_code)


