# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.datarecord import register
from mangrove.datastore.reporter import find_reporter
from mangrove.errors.MangroveException import EntityQuestionAlreadyExistsException, NumberNotRegisteredException, MultipleReportersForANumberException

class TestReporter(TestCase):
    def setUp(self):
        self.manager = get_db_manager('http://localhost:5984/', 'mangrove-test')
        #Register Reporter
        r1 = register(self.manager, entity_type=["Reporter"],
                 data=[("telephone_number", "1234567890"), ("first_name", "A")],
                 location=[],
                 source="sms")
        r2 = register(self.manager, entity_type=["Reporter"],
                 data=[("telephone_number", "8888567890"), ("first_name", "B")],
                 location=[],
                 source="sms")
        r3 = register(self.manager, entity_type=["Reporter"],
                 data=[("telephone_number", "1234567890"), ("first_name", "B")],
                 location=[],
                 source="sms")


    def tearDown(self):
        _delete_db_and_remove_db_manager(self.manager)

    def test_should_load_reporter_list_given_tel_number(self):
        saved_r2 = find_reporter(self.manager,"8888567890")
        self.assertIsNotNone(saved_r2)
        self.assertEqual(1,len(saved_r2))
        self.assertEquals(saved_r2[0]["first_name"],"B")
        self.assertEquals(saved_r2[0]["telephone_number"],"8888567890")

    def test_should_raise_exception_if_no_reporter_for_tel_number(self):
        with self.assertRaises(NumberNotRegisteredException):
            reporter = find_reporter(self.manager,"X")

    def test_should_not_raise_exception_if_multiple_reporters_for_a_number(self):
        reporter_list = find_reporter(self.manager,"1234567890")
        self.assertEqual(2,len(reporter_list))
        self.assertTrue( dict(first_name="A",telephone_number="1234567890") in reporter_list)
        self.assertTrue( dict(first_name="B",telephone_number="1234567890") in reporter_list)




