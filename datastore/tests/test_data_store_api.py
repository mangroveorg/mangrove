# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from mangrove.datastore.entity import Entity, get, get_entities, define_type
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.documents import DataRecordDocument
from pytz import UTC
import unittest

class TestDataStoreApi(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        e = Entity(self.dbm, entity_type="clinic", location=["India","MH","Pune"])
        self.uuid = e.save()

    def tearDown(self):
        del self.dbm.database[self.uuid]
        _delete_db_and_remove_db_manager(self.dbm)

    def test_create_entity(self):
        e = Entity(self.dbm, entity_type="clinic", location=["India","MH","Pune"])
        uuid = e.save()
        self.assertTrue(uuid)
        self.dbm.delete(e._doc)

    def test_get_entity(self):
        e = get(self.dbm, self.uuid)
        self.assertTrue(e.id)
        self.assertTrue(e.type_string == "clinic")

    def test_should_add_location_hierarchy_on_create(self):
        e = Entity(self.dbm, entity_type="clinic", location=["India","MH","Pune"])
        uuid = e.save()
        saved = get(self.dbm, uuid)
        self.assertEqual(saved.location_path,["India","MH","Pune"])

    def test_should_add_entity_type_on_create(self):
        e = Entity(self.dbm, entity_type=["healthfacility","clinic"])
        uuid = e.save()
        saved = get(self.dbm, uuid)
        self.assertEqual(saved.type_path,["healthfacility","clinic"])

    def test_should_add_entity_type_on_create_as_aggregation_tree(self):
        e = Entity(self.dbm, entity_type="health_facility.clinic")
        uuid = e.save()
        saved = get(self.dbm, uuid)
        self.assertEqual(saved.type_path,["health_facility","clinic"])

    def test_should_add_passed_in_hierarchy_path_on_create(self):
        e = Entity(self.dbm, entity_type=["HealthFacility","Clinic"],location=["India","MH","Pune"],aggregation_paths={"org": ["TW_Global","TW_India","TW_Pune"],
                                      "levels": ["Lead Consultant", "Sr. Consultant", "Consultant"]})
        uuid = e.save()
        saved = get(self.dbm, uuid)
        hpath = saved._doc.aggregation_paths
        self.assertEqual(hpath["org"],["TW_Global","TW_India","TW_Pune"])
        self.assertEqual(hpath["levels"],["Lead Consultant", "Sr. Consultant", "Consultant"])

    def test_hierarchy_addition(self):
        e = get(self.dbm, self.uuid)
        org_hierarchy = ["TWGlobal", "TW-India", "TW-Pune"]
        e.set_aggregation_path("org", org_hierarchy)
        e.save()
        saved = get(self.dbm, self.uuid)
        self.assertTrue(saved.aggregation_paths["org"] == ["TWGlobal", "TW-India", "TW-Pune"])

    def test_hierarchy_addition_should_clone_tree(self):
        e = get(self.dbm, self.uuid)
        org_hierarchy = ["TW", "PS", "IS"]
        e.set_aggregation_path("org", org_hierarchy)
        org_hierarchy[0] = ["NewValue"]
        e.save()
        saved = get(self.dbm, self.uuid)
        self.assertTrue(saved.aggregation_paths["org"] == ["TW","PS","IS"])

    def test_save_aggregation_path_only_via_api(self):
        e = get(self.dbm, self.uuid)
        e.location_path[0]="US"
        e.save()
        saved = get(self.dbm, self.uuid)
        self.assertTrue(saved.location_path==["India","MH","Pune"])  # Hierarchy has not changed.

    def test_should_save_hierarchy_tree_only_through_api(self):
        e = get(self.dbm, self.uuid)
        org_hierarchy = ["TW", "PS", "IS"]
        e.set_aggregation_path("org", org_hierarchy)
        e.save()
        e.aggregation_paths['org'][0] = "XYZ"
        e.save()
        saved = get(self.dbm, self.uuid)
        self.assertEqual(saved.aggregation_paths["org"], ["TW","PS","IS"])

    def test_get_entities(self):
        e2 = Entity(self.dbm, "hospital",["India","TN","Chennai"])
        id2 = e2.save()
        entities = get_entities(self.dbm, [self.uuid, id2])
        self.assertEqual(len(entities),2)
        saved = dict([(e.id, e) for e in entities])
        self.assertEqual(saved[id2].type_string, "hospital")
        self.assertEqual(saved[self.uuid].type_string,"clinic")
        self.dbm.delete(e2._doc)

    def _create_clinic_and_reporter(self):
        clinic_entity = Entity(self.dbm, entity_type="clinic",
                               location=["India", "MH", "Pune"])
        clinic_entity.save()
        reporter_entity = Entity(self.dbm, entity_type="reporter")
        reporter_entity.save()
        return clinic_entity, reporter_entity

    def test_add_data_record_to_entity(self):
        clinic_entity, reporter = self._create_clinic_and_reporter()
        data_record = [("medicines", 20), ("doctor", "aroj"), ('facility', 'clinic', 'facility_type'),
                       ('opened_on', datetime(2011,01,02, tzinfo = UTC)),("govt_ref_num","")]
        data_record_id = clinic_entity.add_data(data = data_record,
                                                event_time = datetime(2011,01,02, tzinfo = UTC),
                                                submission_id = "123456")
        self.assertTrue(data_record_id is not None)

        # Assert the saved document structure is as expected
        saved = self.dbm.load(data_record_id, document_class=DataRecordDocument)
        self.assertEqual(saved.data['medicines']['value'], 20)
        self.assertEqual(saved.event_time,datetime(2011,01,02, tzinfo = UTC))
        self.assertEqual(saved.submission_id,"123456")
        self.assertEqual(saved.data['opened_on']['value'],datetime(2011,01,02, tzinfo = UTC))
        self.assertEqual(saved.data['govt_ref_num']['value'],"")

        self.dbm.delete(clinic_entity._doc)
        self.dbm.delete(saved)
        self.dbm.delete(reporter._doc)

    def test_should_create_entity_from_document(self):
        existing = get(self.dbm, self.uuid)
        e = Entity(self.dbm, _document = existing._doc)
        self.assertTrue(e._doc is not None)
        self.assertEqual(e.id,existing.id)
        self.assertEqual(e.type_path,existing.type_path)

    def test_should_fail_create_for_invalid_arguments(self):
        with self.assertRaises(AssertionError):
            Entity(self.dbm, _document = "xyz")

    def test_invalidate_data(self):
        e = Entity(self.dbm, entity_type='store', location=['nyc'])
        e.save()
        data = e.add_data([("apples", 20), ("oranges", 30)])
        valid_doc = self.dbm.load(data)
        self.assertFalse(valid_doc.void)
        e.invalidate_data(data)
        invalid_doc = self.dbm.load(data)
        self.assertTrue(invalid_doc.void)

    def test_invalidate_entity(self):
        e = Entity(self.dbm, entity_type='store', location=['nyc'])
        e.save()
        self.assertFalse(e._doc.void)
        data = [
                [("apples", 20), ("oranges", 30)],
                [("strawberries", 10), ("bananas", 20)]
        ]
        data_ids = []
        for d in data:
            id = e.add_data(d)
            self.assertFalse(self.dbm.load(id).void)
            data_ids.append(id)
        e.invalidate()
        self.assertTrue(e._doc.void)
        for id in data_ids:
            self.assertTrue(self.dbm.load(id).void)


    def test_should_define_entity_type(self):
        e = define_type(self.dbm,["HealthFacility","Clinic"])
        assert (e is not None)
        assert e.id
        self.assertEqual(e.name,["HealthFacility","Clinic"])














