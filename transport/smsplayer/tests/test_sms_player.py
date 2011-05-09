# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from unittest.case import TestCase
from mangrove.transport.smsplayer.smsplayer import SMSPlayer


class TestSMSPlayer(TestCase):
    def test_should_create_sms_player(self):
        s = SMSPlayer()

    def test_should_parse_form_code_from_sms(self):
        pass

    def test_should_parse_answer_dict_from_sms(self):
        pass

    def test_should_parse_answer_list_from_sms(self):
        pass

    def test_should_parse_incomplete_messages_with_no_answer_values(self):
        smsplayer = SMSPlayer()
        form_code, values = smsplayer.parse("WP +ID 1 +BC ")
        self.assertEqual({"ID": "1", "BC": ""}, values)

        form_code, values = smsplayer.parse("WP +ID")
        self.assertEqual({"ID": ""}, values)

        form_code, values = smsplayer.parse("WP")
        self.assertEqual({}, values)
        self.assertEqual("WP", form_code)

    def test_should_preserve_non_leading_white_spaces_in_answer(self):
        smsplayer = SMSPlayer()
        form_code, values = smsplayer.parse("WP +ID 1 +NAME FirstName LastName +AGE 10")
        self.assertEqual({"ID": "1", "NAME": "FirstName LastName", "AGE": "10"}, values)

    def test_should_handle_submission_of_seperator(self):
        smsplayer = SMSPlayer()
        form_code, values = smsplayer.parse("+")
        self.assertEqual({}, values)

    def test_should_handle_submission_of_seperator(self):
        smsplayer = SMSPlayer()
        form_code, values = smsplayer.parse("")
        self.assertEqual({}, values)
        self.assertEqual('', form_code)
