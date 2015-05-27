#vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from unittest import TestCase, SkipTest
from mangrove.errors.MangroveException import SMSParserInvalidFormatException
from mangrove.transport.player.parser import KeyBasedSMSParser
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.form_model import FormModel
from mangrove.transport.player.parser import SMSParser
class TestSMSParser(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.sms_parser = KeyBasedSMSParser(self.dbm)
        

    def test_should_return_form_code(self):
        tokens = ["QUESTIONNAIRE_CODE", "id_1", "FirstName"]
        form_code = self.sms_parser.pop_form_code(tokens)
        self.assertEqual("questionnaire_code", form_code)

    def test_should_return_all_field_codes_in_lower_case(self):
        with patch.object(SMSParser, "get_question_codes") as get_question_codes_mock:
            get_question_codes_mock.return_value = ["id", "name","age"], Mock(spec=FormModel)
            form_code, values, extra = self.sms_parser.parse("WP .id 1 .Name FirstName .aGe 10")
            self.assertEqual({"id": "1", "name": "FirstName", "age": "10"}, values)

    def test_should_preserve_non_leading_white_spaces_in_answer(self):
        with patch.object(SMSParser, "get_question_codes") as get_question_codes_mock:
            get_question_codes_mock.return_value = ["id", "name","age"], Mock(spec=FormModel)
            form_code, values, extra = self.sms_parser.parse("WP .ID 1 .NAME FirstName LastName .AGE 10")
            self.assertEqual({"id": "1", "name": "FirstName LastName", "age": "10"}, values)

    def test_should_parse_incomplete_messages_with_no_answer_values(self):
        with patch.object(SMSParser, "get_question_codes") as get_question_codes_mock:
            get_question_codes_mock.return_value = ["id", "bc"], Mock(spec=FormModel)
            form_code, values, extra = self.sms_parser.parse("WP .ID 1 .BC ")
            self.assertEqual({"id": "1", "bc": ""}, values)

    def test_should_raise_error_if_invalid_sms_format(self):
        with self.assertRaises(SMSParserInvalidFormatException):self.sms_parser.parse("+")

        with self.assertRaises(SMSParserInvalidFormatException):self.sms_parser.parse("  +  ")

        with self.assertRaises(SMSParserInvalidFormatException):self.sms_parser.parse("  +  +")

        with self.assertRaises(SMSParserInvalidFormatException):self.sms_parser.parse("+WP ")

        with self.assertRaises(SMSParserInvalidFormatException):self.sms_parser.parse("WP")

        with self.assertRaises(SMSParserInvalidFormatException):self.sms_parser.parse("WP+")

        with self.assertRaises(SMSParserInvalidFormatException):self.sms_parser.parse(" WP ")

        with self.assertRaises(SMSParserInvalidFormatException):self.sms_parser.parse("WP ID")

        with self.assertRaises(SMSParserInvalidFormatException):self.sms_parser.parse("WP +ID")

    def test_should_accept_only_strings(self):
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(10)
        with self.assertRaises(AssertionError):
            self.sms_parser.parse(None)

    def test_should_accept_unicode(self):
        with patch.object(SMSParser, "get_question_codes") as get_question_codes_mock:
            get_question_codes_mock.return_value = ["s", "n","m", "t"], Mock(spec=FormModel)
            form_code, values, extra = self.sms_parser.parse(u"reg .s Āgra .n شصلكقم .m 080 .t clinic")
            self.assertEqual({u"s": u"Āgra", u"n": u"شصلكقم", u"m": u"080", u"t": u"clinic"}, values)

    def test_should_convert_input_to_unicode(self):
        with patch.object(SMSParser, "get_question_codes") as get_question_codes_mock:
            get_question_codes_mock.return_value = ["s", "n","m", "t"], Mock(spec=FormModel)
            form_code, values, extra = self.sms_parser.parse("reg .s Āgra .n شصلكقم .m 080 .t clinic")
            self.assertEqual({u"s": u"Āgra", u"n": u"شصلكقم", u"m": u"080", u"t": u"clinic"}, values)


    def test_should_ignore_additional_separators(self):
        with patch.object(SMSParser, "get_question_codes") as get_question_codes_mock:
            get_question_codes_mock.return_value = ["ID", "name","age"], Mock(spec=FormModel)
            form_code, values, extra = self.sms_parser.parse(
                "WP .ID 1 . .. .NAME FirstName LastName .. .AGE 10 .. ")
            self.assertEqual({"id": "1", "name": "FirstName LastName", "age": "10"}, values)
            self.assertEqual("wp", form_code)

    def test_should_handle_gps(self):
        with patch.object(SMSParser, "get_question_codes") as get_question_codes_mock:
            get_question_codes_mock.return_value = ["ID", "name","age"], Mock(spec=FormModel)
            form_code, values, extra = self.sms_parser.parse("WP .ID 1 .NAME FirstName.LastName .AGE 10")
            self.assertEqual({"id": "1", "name": "FirstName.LastName", "age": "10"}, values)

    def test_should_return_extra_data(self):
        with patch.object(SMSParser, "get_question_codes") as get_question_codes_mock:
            get_question_codes_mock.return_value = ["name","age"], Mock(spec=FormModel)
            form_code, values, extra = self.sms_parser.parse("WP .NAME FirstName.LastName .AGE 10 .mail test@test.fr")
            self.assertEqual(extra, ["test@test.fr"])
