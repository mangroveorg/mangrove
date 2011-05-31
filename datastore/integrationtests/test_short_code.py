# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.entity import Entity, get_by_short_code, create_entity, generate_short_code, define_type
from mangrove.errors.MangroveException import  DataObjectAlreadyExists, EntityTypeDoesNotExistsException

class TestShortCode(unittest.TestCase):


    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def test_should_create_entity_with_short_code(self):
        define_type(self.dbm, ["Reporter"])
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune", "India"], short_code="REPX")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune", "India"], short_code="REP1")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune", "India"], short_code="REP2")
        reporter.save()

        entity = create_entity(self.dbm, entity_type="Reporter")
        self.assertEqual("Reporter/rep4", entity.id)
        saved_entity = Entity.get(self.dbm, entity.id)
        self.assertEqual(entity.id, saved_entity.id)

        saved_entity = get_by_short_code(self.dbm, short_code="REP4", entity_type=["Reporter"])
        self.assertEqual(saved_entity.id, entity.id)

        entity = create_entity(self.dbm, entity_type=["Reporter"], short_code="ABC")
        saved_entity = get_by_short_code(self.dbm, short_code="ABC", entity_type=["Reporter"])
        self.assertEqual(saved_entity.id, entity.id)

        with self.assertRaises(DataObjectAlreadyExists):
            create_entity(self.dbm, entity_type="Reporter", short_code="ABC")

        entity = create_entity(self.dbm, entity_type="Reporter")
        saved_entity = get_by_short_code(self.dbm, short_code="REP6", entity_type=["Reporter"])
        self.assertEqual(saved_entity.id, entity.id)

        with self.assertRaises(EntityTypeDoesNotExistsException):
            create_entity(self.dbm, entity_type="Dog", short_code="ABC")
        


    def test_should_generate_short_code(self):
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune", "India"], short_code="REPX")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune", "India"], short_code="REP1")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune", "India"], short_code="REP2")
        reporter.save()

        self.assertEqual("rep4", generate_short_code(self.dbm, ["Reporter"]))
        self.assertEqual("cli1", generate_short_code(self.dbm, ["Clinic"]))

    def test_should_get_entity_by_short_code(self):
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune", "India"], id="Reporter/repx")
        reporter.save()

        entity = get_by_short_code(self.dbm, short_code="REPX", entity_type=["Reporter"])
        self.assertTrue(entity is not None)
        self.assertEqual("Reporter/repx", entity.id)

