# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from unittest.case import SkipTest
from mangrove import initializer
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.entity import get_by_short_code
from mangrove.errors.MangroveException import ShortCodeTooLongException
from mangrove.transport.submissions import SubmissionHandler, Request

@SkipTest("To be implemented after register reporter by sms story is played.")
class TestRegisterReporterViaSMS(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        initializer.run(self.dbm)


    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)


    def test_should_register_new_reporter(self):
        text = "REG +N buddy +T Reporter +G 80 80 +D Aaj Tak +M 123456"
        s = SubmissionHandler(self.dbm)
        response = s.accept(Request("sms", text, "1234", "5678"))
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = "REP1"
        self.assertEqual(response.short_code, expected_short_code)
        a = get_by_short_code(self.dbm, expected_short_code, ["Reporter"])
        self.assertEqual(a.short_code, expected_short_code)


    def test_should_throw_exception_if_invalid_short_code(self):
        text = "REG +S toolongtestreporter +N buddy +T Reporter +G 80 80 +D Aaj Tak +M 123456"
        s = SubmissionHandler(self.dbm)
        with self.assertRaises(ShortCodeTooLongException):
            response = s.accept(Request("sms", text, "1234", "5678"))
