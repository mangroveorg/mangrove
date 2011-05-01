# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock
from mangrove.datastore.database import DatabaseManager
from mangrove.transport.smsplayer.smsplayer import SMSPlayer
from mangrove.transport.submissions import Request

class TestSMSPlayer(TestCase):
    def test_should_create_sms_player(self):
        dbm = Mock(spec = DatabaseManager)
        request = Request(transport = "sms",message = "hello world",source = "1234", destination = "5678")
        s = SMSPlayer(dbm)

    def test_should_parse_form_code_from_sms(self):
        pass

    def test_should_parse_answer_dict_from_sms(self):
        pass

    def test_should_parse_answer_list_from_sms(self):
        pass
