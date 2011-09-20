# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.entity import Entity, get_by_short_code, create_entity, get_all_entities
from mangrove.datastore.entity_type import define_type
from mangrove.errors.MangroveException import  DataObjectAlreadyExists, EntityTypeDoesNotExistsException, DataObjectNotFound


class TestShortCode(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        self.reporter_entity_type = ["Reporter"]
        define_type(self.dbm, self.reporter_entity_type)
        self.reporter1 = Entity(self.dbm, entity_type=self.reporter_entity_type, location=["Pune", "India"], short_code="REPX")
        self.reporter1.save()
        self.reporter2 = Entity(self.dbm, entity_type=self.reporter_entity_type, location=["Pune", "India"], short_code="REP1")
        self.reporter2.save()
        self.reporter3 = Entity(self.dbm, entity_type=self.reporter_entity_type, location=["Pune", "India"], short_code="REP2")
        self.reporter3.save()

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def test_create_entity(self):
        e = Entity(self.dbm, entity_type="clinic", location=["India", "MH", "Pune"])
        uuid = e.save()
        self.assertTrue(uuid)
        self.dbm.delete(e)

    def test_create_entity_with_id(self):
        e = Entity(self.dbm, entity_type="clinic", location=["India", "MH", "Pune"], id="-1000")
        uuid = e.save()
        self.assertEqual(uuid, "-1000")
        self.dbm.delete(e)

    def test_get_entity(self):
        e = get(self.dbm, self.reporter1.id)
        self.assertTrue(e.id)
        self.assertTrue(e.type_string == self.reporter_entity_type[0])

    def test_should_add_location_hierarchy_on_create(self):
        e = Entity(self.dbm, entity_type="clinic", location=["India", "MH", "Pune"])
        uuid = e.save()
        saved = get(self.dbm, uuid)
        self.assertEqual(saved.location_path, ["India", "MH", "Pune"])

    def test_should_return_empty_list_if_location_path_is_not_stored(self):
        e = Entity(self.dbm, entity_type="clinic")
        uuid = e.save()
        saved = get(self.dbm, uuid)
        self.assertEqual(saved.location_path, [])

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

    def test_should_get_all_entities(self):
        entities = get_all_entities(self.dbm)
        self.assertEqual(3,len(entities))
        self.assertEqual("REP1",entities[0].short_code)
        self.assertEqual("REP2",entities[1].short_code)
        self.assertEqual("REPX",entities[2].short_code)

    def test_hierarchy_addition(self):
        e = get(self.dbm, self.reporter1.id)
        org_hierarchy = ["TWGlobal", "TW-India", "TW-Pune"]
        e.set_aggregation_path("org", org_hierarchy)
        e.save()
        saved = get(self.dbm, self.reporter1.id)
        self.assertTrue(saved.aggregation_paths["org"] == ["TWGlobal", "TW-India", "TW-Pune"])

    def test_hierarchy_addition_should_clone_tree(self):
        e = get(self.dbm, self.reporter1.id)
        org_hierarchy = ["TW", "PS", "IS"]
        e.set_aggregation_path("org", org_hierarchy)
        org_hierarchy[0] = ["NewValue"]
        e.save()
        saved = get(self.dbm, self.reporter1.id)
        self.assertTrue(saved.aggregation_paths["org"] == ["TW", "PS", "IS"])

    def test_save_aggregation_path_only_via_api(self):
        e = get(self.dbm, self.reporter1.id)
        e.location_path[0] = "US"
        e.save()
        saved = get(self.dbm, self.reporter1.id)
        print saved.location_path
        self.assertTrue(saved.location_path == ["Pune", "India"])  # Hierarchy has not changed.

    def test_should_save_hierarchy_tree_only_through_api(self):
        e = get(self.dbm, self.reporter1.id)
        org_hierarchy = ["TW", "PS", "IS"]
        e.set_aggregation_path("org", org_hierarchy)
        e.save()
        e.aggregation_paths['org'][0] = "XYZ"
        e.save()
        saved = get(self.dbm, self.reporter1.id)
        self.assertEqual(saved.aggregation_paths["org"], ["TW", "PS", "IS"])

    def test_get_entities(self):
        e2 = Entity(self.dbm, "hospital", ["India", "TN", "Chennai"])
        id2 = e2.save()
        entities = get_entities(self.dbm, [self.reporter1.id, id2])
        self.assertEqual(len(entities), 2)
        saved = dict([(e.id, e) for e in entities])
        self.assertEqual(saved[id2].type_string, "hospital")
        self.assertEqual(saved[self.reporter1.id].type_string, self.reporter_entity_type[0])
        self.dbm.delete(e2)

    def test_should_add_passed_in_hierarchy_path_on_create(self):
        e = Entity(self.dbm, entity_type=["HealthFacility", "Clinic"], location=["India", "MH", "Pune"],
                   aggregation_paths={"org": ["TW_Global", "TW_India", "TW_Pune"],
                                      "levels": ["Lead Consultant", "Sr. Consultant", "Consultant"]})
        uuid = e.save()
        saved = get(self.dbm, uuid)
        hpath = saved._doc.aggregation_paths
        self.assertEqual(hpath["org"], ["TW_Global", "TW_India", "TW_Pune"])
        self.assertEqual(hpath["levels"], ["Lead Consultant", "Sr. Consultant", "Consultant"])

    def test_should_add_entity_type_on_create(self):
        e = Entity(self.dbm, entity_type=["healthfacility", "clinic"])
        uuid = e.save()
        saved = get(self.dbm, uuid)
        self.assertEqual(saved.type_path, ["healthfacility", "clinic"])

    def test_should_add_entity_type_on_create_as_aggregation_tree(self):
        e = Entity(self.dbm, entity_type="health_facility")
        uuid = e.save()
        saved = get(self.dbm, uuid)
        self.assertEqual(saved.type_path, ["health_facility"])

    def test_should_add_passed_in_hierarchy_path_on_create(self):
        e = Entity(self.dbm, entity_type=["HealthFacility", "Clinic"], location=["India", "MH", "Pune"],
                   aggregation_paths={"org": ["TW_Global", "TW_India", "TW_Pune"],
                                      "levels": ["Lead Consultant", "Sr. Consultant", "Consultant"]})
        uuid = e.save()
        saved = get(self.dbm, uuid)
        hpath = saved._doc.aggregation_paths
        self.assertEqual(hpath["org"], ["TW_Global", "TW_India", "TW_Pune"])
        self.assertEqual(hpath["levels"], ["Lead Consultant", "Sr. Consultant", "Consultant"])

    def test_should_create_entity_from_document(self):
        existing = self.dbm.get(self.reporter1.id, Entity)
        e = Entity.new_from_doc(self.dbm, existing._doc)
        self.assertTrue(e._doc is not None)
        self.assertEqual(e.id, existing.id)
        self.assertEqual(e.type_path, existing.type_path)

def get_entities(dbm, ids):
    return dbm.get_many(ids, Entity)

# Adaptor methods to old api
def get(dbm, id):
    return dbm.get(id, Entity)
