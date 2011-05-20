# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.entity import Entity, _get_entity_count_for_type, get_by_short_code

class TestShortCode(unittest.TestCase):


    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def test_should_return_count_of_given_entity_type(self):
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune", "India"], short_code="REPX")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune", "India"], short_code="REP1")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune", "India"], short_code="REP2")
        reporter.save()
        codes = _get_entity_count_for_type(self.dbm, "Reporter")
        self.assertEqual(codes, 3)

        codes = _get_entity_count_for_type(self.dbm, "Clinic")
        self.assertEqual(codes, 0)


    def test_get_entities_by_type(self):
        e = Entity(self.dbm, entity_type='foo', short_code="WAR")
        e.save()
        loaded_entity = get_by_short_code(self.dbm, e.short_code)
        self.assertTrue(loaded_entity)
        self.assertEqual(loaded_entity.aggregation_paths.get('_type'), ['foo'])
        self.assertEqual(loaded_entity.short_code, 'WAR')

