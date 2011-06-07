# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from unittest.case import SkipTest
from mangrove import initializer
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.datadict import DataDictType
from mangrove.datastore.entity import get_by_short_code, create_entity
from mangrove.errors.MangroveException import ShortCodeTooLongException
from mangrove.form_model.form_model import MOBILE_NUMBER_FIELD, NAME_FIELD
from mangrove.transport.submissions import SubmissionHandler, Request


class TestRegisterReporterViaSMS(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        initializer.run(self.dbm)
        self.name_type = DataDictType(self.dbm, name='Name', slug='name', primitive_type='string')
        self.telephone_number_type = DataDictType(self.dbm, name='telephone_number', slug='telephone_number', primitive_type='string')
        self.name_type.save()
        self.telephone_number_type.save()
        reporter = create_entity(self.dbm, entity_type=["Reporter"],
                        location=["India", "Pune"], aggregation_paths=None, short_code="REP1",
                            )
        reporter.add_data(data=[(MOBILE_NUMBER_FIELD, '1234', self.telephone_number_type),
                                  (NAME_FIELD, "Test_reporter", self.name_type)], submission=dict(submission_id="2"))



    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    @SkipTest
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

    @SkipTest
    def test_should_throw_exception_if_invalid_short_code(self):
        text = "REG +S toolongtestreporter +N buddy +T Reporter +G 80 80 +D Aaj Tak +M 123456"
        s = SubmissionHandler(self.dbm)
        with self.assertRaises(ShortCodeTooLongException):
            response = s.accept(Request("sms", text, "1234", "5678"))

    def test_should_register_new_reporter_with_case_insensitive_type(self):
        text = "REG +N buddy +T reporter +G 80 80 +D Aaj Tak +M 123456"
        s = SubmissionHandler(self.dbm)
        response = s.accept(Request("sms", text, "1234", "5678"))
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = "rep1"
        self.assertEqual(response.short_code, expected_short_code)
        a = get_by_short_code(self.dbm, expected_short_code, ["reporter"])
        self.assertEqual(a.short_code, expected_short_code)
