import unittest
from mangrove.transport.player.parser import SMSParserFactory, OrderSMSParser, KeyBasedSMSParser

class TestSMSParserFactory(unittest.TestCase):
    def test_order_sms(self):
        message = "questionnaire_code q1_answer q2_answer q3_answer"
        sms_parser = SMSParserFactory().getSMSParser(dbm={1:"duck typing"},message=message)
        self.assertEqual(OrderSMSParser,type(sms_parser))
        self.assertEqual("duck typing",sms_parser.dbm[1])

    def test_keyword_based_sms(self):
        message = "questionnaire_code .q1 q1_answer .q2 q2_answer .q3 q3_answer"
        sms_parser = SMSParserFactory().getSMSParser(message=message)
        self.assertEqual(KeyBasedSMSParser,type(sms_parser))
