# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.entity import Entity
from mangrove.datastore.entity_type import get_all_entity_types, define_type
from mangrove.errors.MangroveException import EntityTypeAlreadyDefined

class TestEntityType(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        e = Entity(self.dbm, entity_type="clinic", location=["India", "MH", "Pune"])
        self.uuid = e.save()

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def test_should_define_entity_type(self):
        entity_type = ["HealthFacility", "Clinic"]
        entity_types = get_all_entity_types(self.dbm)
        self.assertNotIn(entity_type, entity_types)
        define_type(self.dbm, entity_type)
        types = get_all_entity_types(self.dbm)
        self.assertIn(entity_type, types)
        self.assertIn([entity_type[0]], types)

    def test_should_throw_assertionError_if_entity_type_is_not_list(self):
        with self.assertRaises(AssertionError):
            entity_type = "HealthFacility"
            define_type(self.dbm, entity_type)

    def test_should_disallow_redefining_the_same_entity(self):
        define_type(self.dbm, ["HealthFacility", "Clinic"])
        with self.assertRaises(EntityTypeAlreadyDefined):
            define_type(self.dbm, ["HealthFacility", "Clinic"])

    def test_should_disallow_redefining_the_same_entity_with_different_case(self):
        define_type(self.dbm, ["HealthFacility", "Clinic"])
        with self.assertRaises(EntityTypeAlreadyDefined):
            define_type(self.dbm, ["healTHfaciLIty", "clinic"])

    def test_should_define_single_entity(self):
        define_type(self.dbm, ["Clinic"])
        entity_types = get_all_entity_types(self.dbm)
        self.assertListEqual(entity_types, [["Clinic"]])

    def test_should_load_all_entity_types(self):
        define_type(self.dbm, ["HealthFacility", "Clinic"])
        define_type(self.dbm, ["HealthFacility", "Hospital"])
        define_type(self.dbm, ["WaterPoint", "Lake"])
        define_type(self.dbm, ["WaterPoint", "Dam"])
        entity_types = get_all_entity_types(self.dbm)

        expected = [['HealthFacility'],
            ['HealthFacility', 'Clinic'],
            ['HealthFacility', 'Hospital'],
            ['WaterPoint'],
            ['WaterPoint', 'Lake'],
            ['WaterPoint', 'Dam']]

        for e in expected:
            self.assertIn(e, entity_types)
