# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.entity import create_entity
from mangrove.datastore.entity_type import define_type
from mangrove.datastore.queries import get_entity_count_for_type

class TestQueries(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)


    def test_get_entity_count_for_type(self):
        entity_type = "Clinic"
        define_type(self.dbm,[entity_type])
        create_entity(self.dbm, [entity_type],"1")
        self.assertEqual(1,get_entity_count_for_type(self.dbm,entity_type))


