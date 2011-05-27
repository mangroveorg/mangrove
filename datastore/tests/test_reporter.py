# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.datarecord import register
from mangrove.datastore.reporter import find_reporter
from mangrove.errors.MangroveException import  NumberNotRegisteredException
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.form_model import MOBILE_NUMBER_FIELD, NAME_FIELD


class TestReporter(TestCase):
    def setUp(self):
        self.manager = get_db_manager('http://localhost:5984/', 'mangrove-test')
        self.phone_number_type = DataDictType(self.manager, name='Telephone Number', slug='telephone_number',
                                              primitive_type='string')
        self.first_name_type = DataDictType(self.manager, name='First Name', slug='first_name', primitive_type='string')
        #Register Reporter
        register(self.manager, entity_type=["Reporter"],
                 data=[(MOBILE_NUMBER_FIELD, "1234567890", self.phone_number_type),
                       (NAME_FIELD, "A", self.first_name_type)],
                 location=[],
                 source="sms")
        register(self.manager, entity_type=["Reporter"],
                 data=[(MOBILE_NUMBER_FIELD, "8888567890", self.phone_number_type),
                       (NAME_FIELD, "B", self.first_name_type)],
                 location=[],
                 source="sms")
        register(self.manager, entity_type=["Reporter"],
                 data=[(MOBILE_NUMBER_FIELD, "1234567890", self.phone_number_type),
                       (NAME_FIELD, "B", self.first_name_type)],
                 location=[],
                 source="sms")

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.manager)

    def test_should_load_reporter_list_given_tel_number(self):
        saved_r2 = find_reporter(self.manager, "8888567890")
        self.assertIsNotNone(saved_r2)
        self.assertEqual(1, len(saved_r2))
        self.assertEquals(saved_r2[0]["name"], "B")
        self.assertEquals(saved_r2[0]["mobile_number"], "8888567890")

    def test_should_raise_exception_if_no_reporter_for_tel_number(self):
        with self.assertRaises(NumberNotRegisteredException):
            find_reporter(self.manager, "X")

    def test_should_not_raise_exception_if_multiple_reporters_for_a_number(self):
        reporter_list = find_reporter(self.manager, "1234567890")
        self.assertEqual(2, len(reporter_list))
        self.assertTrue({NAME_FIELD: "A", MOBILE_NUMBER_FIELD: "1234567890"} in reporter_list)
        self.assertTrue({NAME_FIELD: "B", MOBILE_NUMBER_FIELD: "1234567890"} in reporter_list)


