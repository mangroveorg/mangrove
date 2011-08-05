# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.entity import Entity, get_by_short_code, create_entity, define_type
from mangrove.errors.MangroveException import  DataObjectAlreadyExists, EntityTypeDoesNotExistsException, DataObjectNotFound


class TestShortCode(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        define_type(self.dbm, ["Reporter"])
        reporter = Entity(self.dbm, entity_type=["Reporter"], location=["Pune", "India"], short_code="REPX")
        reporter.save()
        reporter = Entity(self.dbm, entity_type=["Reporter"], location=["Pune", "India"], short_code="REP1")
        reporter.save()
        reporter = Entity(self.dbm, entity_type=["Reporter"], location=["Pune", "India"], short_code="REP2")
        reporter.save()

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def test_should_create_entity_with_short_code(self):
        with self.assertRaises(AssertionError):
            entity = create_entity(self.dbm, entity_type=["reporter"], short_code=None)

        with self.assertRaises(AssertionError):
            entity = create_entity(self.dbm, entity_type=["reporter"], short_code="")

        with self.assertRaises(AssertionError):
            entity = create_entity(self.dbm, entity_type="Reporter", short_code="BLAH")
        with self.assertRaises(AssertionError):
            entity = create_entity(self.dbm, entity_type=[], short_code="BLAH")
        with self.assertRaises(AssertionError):
            entity = create_entity(self.dbm, entity_type=("reporter"), short_code="BLAH")

        entity = create_entity(self.dbm, entity_type=["reporter"], short_code="ABC")
        saved_entity = get_by_short_code(self.dbm, short_code="ABC", entity_type=["reporter"])
        self.assertEqual(saved_entity.id, entity.id)

        with self.assertRaises(DataObjectAlreadyExists):
            create_entity(self.dbm, entity_type=["reporter"], short_code="ABC")

        with self.assertRaises(EntityTypeDoesNotExistsException):
            create_entity(self.dbm, entity_type=["Dog"], short_code="ABC")


    def test_should_get_entity_by_short_code(self):
        reporter = Entity(self.dbm, entity_type=["Reporter"], location=["Pune", "India"], short_code="repx")
        reporter.save()

        entity = get_by_short_code(self.dbm, short_code="repx", entity_type=["Reporter"])
        self.assertTrue(entity is not None)
        self.assertEqual("repx", entity.short_code)

        with self.assertRaises(DataObjectNotFound):
            entity = get_by_short_code(self.dbm, short_code="ABC", entity_type=["Waterpoint"])



