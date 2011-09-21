# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import  datetime
from unittest.case import TestCase
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.entity import create_entity
from mangrove.datastore.entity_type import define_type
from mangrove.errors.MangroveException import  NumberNotRegisteredException
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.form_model import MOBILE_NUMBER_FIELD, NAME_FIELD
from mangrove.transport.player.player import TransportInfo
from mangrove.transport.reporter import find_reporter, reporters_submitted_data
from mangrove.transport.submissions import Submission


class TestReporter(TestCase):
    def register(self, manager, entity_type, data, location, source, aggregation_paths=None, short_code=None):
    #    manager = get_db_manager()
        e = create_entity(manager, entity_type=entity_type, location=location, aggregation_paths=aggregation_paths,
                          short_code=short_code)
        e.add_data(data=data)
        return e

    def setUp(self):
        self.manager = get_db_manager('http://localhost:5984/', 'mangrove-test')
        define_type(self.manager, ["reporter"])
        self.phone_number_type = DataDictType(self.manager, name='Telephone Number', slug='telephone_number',
                                              primitive_type='string')
        self.first_name_type = DataDictType(self.manager, name='First Name', slug='first_name',
                                            primitive_type='string')
        #Register Reporter
        self.register(self.manager, entity_type=["reporter"],
                      data=[(MOBILE_NUMBER_FIELD, "1234567890", self.phone_number_type),
                          (NAME_FIELD, "A", self.first_name_type)],
                      location=[],
                      source="sms", short_code="REP1")
        self.register(self.manager, entity_type=["reporter"],
                      data=[(MOBILE_NUMBER_FIELD, "8888567890", self.phone_number_type),
                          (NAME_FIELD, "B", self.first_name_type)],
                      location=[],
                      source="sms", short_code="rep5")
        self.register(self.manager, entity_type=["reporter"],
                      data=[(MOBILE_NUMBER_FIELD, "1234567890", self.phone_number_type),
                          (NAME_FIELD, "B", self.first_name_type)],
                      location=[],
                      source="sms", short_code="REP2")

        self.register(self.manager, entity_type=["reporter"],
                      data=[(MOBILE_NUMBER_FIELD, "1234567891", self.phone_number_type),
                          (NAME_FIELD, "C", self.first_name_type)],
                      location=[],
                      source="sms", short_code="REP3")

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

    def test_should_return_reporter_submitted_data(self):
        Submission(self.manager, TransportInfo('sms', '8888567890', '123'), 'test').save()
        reporters = reporters_submitted_data(self.manager, 'test')
        self.assertEqual(1,len(reporters))
        self.assertEqual('8888567890', reporters[0].value('mobile_number'))

    def test_should_return_reporter_submitted_data_in_a_time_period(self):
        submission1= Submission(self.manager, TransportInfo('sms', '8888567890', '123'), 'test')
        submission1._doc.event_time = datetime(2011,2,2)
        submission1.save()

        submission2 = Submission(self.manager, TransportInfo('sms', '1234567891', '123'), 'test')
        submission2._doc.event_time = datetime(2011,1,1)
        submission2.save()

        from_time = datetime(2011,2,1)
        to_time = datetime(2011,2,27)
        reporters = reporters_submitted_data(self.manager, 'test',from_time,to_time)
        self.assertEqual(1,len(reporters))
        self.assertEqual('8888567890', reporters[0].value('mobile_number'))

