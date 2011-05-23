# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.entity import Entity, _get_entity_count_for_type, get_by_short_code, create_entity
from mangrove.errors.MangroveException import ShortCodeAlreadyInUseException

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

        entity = create_entity(self.dbm, entity_type="Reporter")
        saved_entity = get_by_short_code(self.dbm, "REP4")
        self.assertEqual(saved_entity.id, entity.id)

        entity = create_entity(self.dbm, entity_type="Reporter", short_code="ABC")
        saved_entity = get_by_short_code(self.dbm, "ABC")
        self.assertEqual(saved_entity.id, entity.id)

        with self.assertRaises(ShortCodeAlreadyInUseException):
            create_entity(self.dbm, entity_type="Reporter", short_code="ABC")

        entity = create_entity(self.dbm, entity_type="Reporter")
        saved_entity = get_by_short_code(self.dbm, "REP6")
        self.assertEqual(saved_entity.id, entity.id)

