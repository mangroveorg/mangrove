
from datetime import datetime
import unittest
from mock import Mock, patch
from pytz import UTC
from mangrove.datastore.entity import Entity, get_by_short_code, create_entity, get_all_entities, DataRecord, void_entity, get_by_short_code_include_voided
from mangrove.datastore.tests.test_data import TestData
from mangrove.errors.MangroveException import DataObjectAlreadyExists, EntityTypeDoesNotExistsException, DataObjectNotFound, FailedToSaveDataObject
from mangrove.utils.test_utils.database_utils import create_dbmanager_for_ut, safe_define_type, ut_reporter_id
from mangrove.datastore.database import _delete_db_and_remove_db_manager
from mangrove.datastore.cache_manager import get_cache_manager


class TestEntity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_dbmanager_for_ut(cls)
        cls.test_data = TestData(cls.manager)

    @classmethod
    def tearDownClass(cls):
        _delete_db_and_remove_db_manager(cls.manager)
        get_cache_manager().flush_all()

    def test_create_entity(self):
        e = Entity(self.manager, entity_type="clinic", location=["India", "MH", "Pune"])
        uuid = e.save()
        self.assertTrue(uuid)
        self.manager.delete(e)

    def test_should_throw_excption_when_voiding_entity_which_has_been_updated_by_others(self):
        e = Entity(self.manager, entity_type="clinic", location=["India", "MH", "Pune"])
        uuid = e.save()
        entity1 = self.manager.get(uuid, Entity)
        entity2 = self.manager.get(uuid, Entity)

        with self.assertRaises(FailedToSaveDataObject) as e:
            entity1.void()
            entity2.void()

        self.assertTrue("ResourceConflict" in e.exception.message)

        self.manager.delete(entity1)

    def test_should_invalidate_entity(self):
        short_code = "short_code"
        entity_type = ["clinic"]
        e = Entity(self.manager, entity_type=entity_type, location=["India", "MH", "Pune"], short_code=short_code)
        uuid = e.save()
        self.assertTrue(uuid)
        void_entity(self.manager, entity_type, short_code)
        with self.assertRaises(DataObjectNotFound):
            get_by_short_code(self.manager, short_code, entity_type)
            
    def _add_data(self,e):
        data = [('beds', 10), ('meds', 20)]
        data_record_id1 = e.add_data(data=data)
        data = [('patients', 10), ('meds', 10)]
        data_record_id2 = e.add_data(data=data)
        data = [('beds', 20), ('patients', 20)]
        data_record_id3 = e.add_data(data=data)
        return data_record_id1, data_record_id2, data_record_id3

    def _get_data_records(self, data_record_id1, data_record_id2, data_record_id3):
        data_record1 = DataRecord.get(self.manager, data_record_id1)
        data_record2 = DataRecord.get(self.manager, data_record_id2)
        data_record3 = DataRecord.get(self.manager, data_record_id3)
        return data_record1, data_record2, data_record3

    def test_should_invalidate_entity_without_its_data_records(self):
        short_code = "short_code"
        entity_type = ["clinic"]
        e = Entity(self.manager, entity_type=entity_type, location=["India", "MH", "Pune"], short_code=short_code)
        uuid = e.save()
        self.assertTrue(uuid)

        data_record_id1, data_record_id2, data_record_id3 = self._add_data(e)

        void_entity(self.manager, entity_type, short_code)
        with self.assertRaises(DataObjectNotFound):
            get_by_short_code(self.manager, short_code, entity_type)

        data_record1, data_record2, data_record3 = self._get_data_records(data_record_id1, data_record_id2,
                                                                          data_record_id3)
        self.assertFalse(data_record1.is_void())
        self.assertFalse(data_record2.is_void())
        self.assertFalse(data_record3.is_void())

    def test_should_invalidate_entity_when_entity_type_is_string(self):
        short_code = "short_code"
        entity_type = "clinic"
        e = Entity(self.manager, entity_type=entity_type, location=["India", "MH", "Pune"], short_code=short_code)
        uuid = e.save()
        self.assertTrue(uuid)
        void_entity(self.manager, entity_type, short_code)
        with self.assertRaises(DataObjectNotFound):
            get_by_short_code(self.manager, short_code, [entity_type])

    def test_create_entity_with_id(self):
        e = Entity(self.manager, entity_type="clinic", location=["India", "MH", "Pune"], id="-1000")
        uuid = e.save()
        self.assertEqual(uuid, "-1000")
        self.manager.delete(e)

    def test_get_entity(self):
        test_data = self.test_data
        e = get(self.manager, test_data.entity1.id)
        self.assertTrue(e.id)
        print e.type_string
        self.assertTrue(e.type_string == test_data.entity_type_string)

    def test_should_add_location_hierarchy_on_create(self):
        e = Entity(self.manager, entity_type="clinic", location=["India", "MH", "Pune"])
        uuid = e.save()
        saved = get(self.manager, uuid)
        self.assertEqual(saved.location_path, ["India", "MH", "Pune"])

    def test_should_return_empty_list_if_location_path_is_not_stored(self):
        e = Entity(self.manager, entity_type="clinic")
        uuid = e.save()
        saved = get(self.manager, uuid)
        self.assertEqual(saved.location_path, [])

    def test_should_create_entity_with_short_code(self):
        with self.assertRaises(AssertionError):
            create_entity(self.manager, entity_type=["reporter"], short_code=None)

        with self.assertRaises(AssertionError):
            create_entity(self.manager, entity_type=["reporter"], short_code="")

        with self.assertRaises(AssertionError):
            create_entity(self.manager, entity_type="Reporter", short_code="BLAH")
        with self.assertRaises(AssertionError):
            create_entity(self.manager, entity_type=[], short_code="BLAH")
        with self.assertRaises(AssertionError):
            create_entity(self.manager, entity_type=("reporter"), short_code="BLAH")

        safe_define_type(self.manager, ["reporter"])
        short_code = ut_reporter_id()
        entity = create_entity(self.manager, entity_type=["reporter"], short_code=short_code)
        saved_entity = get_by_short_code(self.manager, short_code=short_code, entity_type=["reporter"])
        self.assertEqual(saved_entity.id, entity.id)

        with self.assertRaises(DataObjectAlreadyExists):
            create_entity(self.manager, entity_type=["reporter"], short_code=short_code)

        with self.assertRaises(EntityTypeDoesNotExistsException):
            create_entity(self.manager, entity_type=["Dog"], short_code=short_code)

    def test_should_raise_exception_if_void_entity_with_same_short_code_exists(self):
        entity_type = ["reporter"]
        safe_define_type(self.manager, entity_type)
        short_code = ut_reporter_id()
        entity = create_entity(self.manager, entity_type=entity_type, short_code=short_code)
        saved_entity = get_by_short_code(self.manager, short_code=short_code, entity_type=entity_type)
        self.assertEqual(saved_entity.id, entity.id)

        void_entity(self.manager, entity_type, short_code)
        with self.assertRaises(DataObjectAlreadyExists):
            create_entity(self.manager, entity_type=entity_type, short_code=short_code)


    def test_should_get_entity_by_short_code(self):
        reporter = Entity(self.manager, entity_type=["Reporter"], location=["Pune", "India"], short_code="repx")
        reporter.save()

        entity = get_by_short_code(self.manager, short_code="repx", entity_type=["Reporter"])
        self.assertIsNotNone(entity)
        self.assertEqual("repx", entity.short_code)

        with self.assertRaises(DataObjectNotFound):
            get_by_short_code(self.manager, short_code="ABC", entity_type=["Waterpoint"])

    def test_should_get_entity_by_short_code_including_voided(self):
        short_code = ut_reporter_id()
        entity_type = ["Reporter"]
        reporter = Entity(self.manager, entity_type=entity_type, location=["Pune", "India"], short_code=short_code)
        reporter.save()

        entity = get_by_short_code_include_voided(self.manager, short_code=short_code, entity_type=entity_type)
        self.assertEqual(short_code, entity.short_code)
        self.assertFalse(entity.is_void())

        void_entity(self.manager, entity_type, short_code)

        with self.assertRaises(DataObjectNotFound):
            get_by_short_code(self.manager, short_code, entity_type)

        entity = get_by_short_code_include_voided(self.manager, short_code=short_code, entity_type=entity_type)
        self.assertEqual(short_code, entity.short_code)
        self.assertTrue(entity.is_void())

    def test_should_get_all_entities(self):
        entities = get_all_entities(self.manager)
        self.assertLess(0, len(entities))

    def test_should_get_all_entities_of_type(self):
        test_data = self.test_data
        entities_before = get_all_entities(self.manager, test_data.ENTITY_TYPE)
        reporter = Entity(self.manager, entity_type=test_data.ENTITY_TYPE, location=["Pune", "India"], short_code=ut_reporter_id())
        reporter.save()
        entities = get_all_entities(self.manager, test_data.ENTITY_TYPE)
        self.assertEqual(len(entities_before)+1, len(entities))

    def test_hierarchy_addition(self):
        e = get(self.manager, self.test_data.entity1.id)
        org_hierarchy = ["TWGlobal", "TW-India", "TW-Pune"]
        e.set_aggregation_path("org", org_hierarchy)
        e.save()
        saved = get(self.manager, self.test_data.entity1.id)
        self.assertTrue(saved.aggregation_paths["org"] == ["TWGlobal", "TW-India", "TW-Pune"])

    def test_hierarchy_addition_should_clone_tree(self):
        test_data = self.test_data
        e = get(self.manager, test_data.entity1.id)
        org_hierarchy = ["TW", "PS", "IS"]
        e.set_aggregation_path("org", org_hierarchy)
        org_hierarchy[0] = ["NewValue"]
        e.save()
        saved = get(self.manager, test_data.entity1.id)
        self.assertTrue(saved.aggregation_paths["org"] == ["TW", "PS", "IS"])

    def test_save_aggregation_path_only_via_api(self):
        test_data = self.test_data
        e = get(self.manager, test_data.entity1.id)
        e.location_path[0] = "US"
        e.save()
        saved = get(self.manager, test_data.entity1.id)
        self.assertTrue(saved.location_path == [u'India', u'MH', u'Pune'])  # Hierarchy has not changed.

    def test_should_save_hierarchy_tree_only_through_api(self):
        test_data = self.test_data
        e = get(self.manager, test_data.entity1.id)
        org_hierarchy = ["TW", "PS", "IS"]
        e.set_aggregation_path("org", org_hierarchy)
        e.save()
        e.aggregation_paths['org'][0] = "XYZ"
        e.save()
        saved = get(self.manager, test_data.entity1.id)
        self.assertEqual(saved.aggregation_paths["org"], ["TW", "PS", "IS"])

    def test_get_entities(self):
        e2 = Entity(self.manager, "hospital", ["India", "TN", "Chennai"])
        id2 = e2.save()
        entities = get_entities(self.manager, [self.test_data.entity1.id, id2])
        self.assertEqual(len(entities), 2)
        saved = dict([(e.id, e) for e in entities])
        self.assertEqual(saved[id2].type_string, "hospital")
        self.assertEqual(saved[self.test_data.entity1.id].type_string, self.test_data.entity_type_string)
        self.manager.delete(e2)

    def test_should_add_passed_in_hierarchy_path_on_create(self):
        e = Entity(self.manager, entity_type=["HealthFacility", "Clinic"], location=["India", "MH", "Pune"],
                   aggregation_paths={"org": ["TW_Global", "TW_India", "TW_Pune"],
                                      "levels": ["Lead Consultant", "Sr. Consultant", "Consultant"]})
        uuid = e.save()
        saved = get(self.manager, uuid)
        hpath = saved._doc.aggregation_paths
        self.assertEqual(hpath["org"], ["TW_Global", "TW_India", "TW_Pune"])
        self.assertEqual(hpath["levels"], ["Lead Consultant", "Sr. Consultant", "Consultant"])

    def test_should_add_entity_type_on_create(self):
        e = Entity(self.manager, entity_type=["healthfacility", "clinic"])
        uuid = e.save()
        saved = get(self.manager, uuid)
        self.assertEqual(saved.type_path, ["healthfacility", "clinic"])

    def test_should_add_entity_type_on_create_as_aggregation_tree(self):
        e = Entity(self.manager, entity_type="health_facility")
        uuid = e.save()
        saved = get(self.manager, uuid)
        self.assertEqual(saved.type_path, ["health_facility"])

    def test_should_add_passed_in_hierarchy_path_on_create(self):
        e = Entity(self.manager, entity_type=["HealthFacility", "Clinic"], location=["India", "MH", "Pune"],
                   aggregation_paths={"org": ["TW_Global", "TW_India", "TW_Pune"],
                                      "levels": ["Lead Consultant", "Sr. Consultant", "Consultant"]})
        uuid = e.save()
        saved = get(self.manager, uuid)
        hpath = saved._doc.aggregation_paths
        self.assertEqual(hpath["org"], ["TW_Global", "TW_India", "TW_Pune"])
        self.assertEqual(hpath["levels"], ["Lead Consultant", "Sr. Consultant", "Consultant"])

    def reload_entity(self, entity):
        return self.manager.get(entity.id, Entity)

    def test_should_create_entity_from_document(self):
        existing = self.reload_entity(self.test_data.entity1)
        e = Entity.new_from_doc(self.manager, existing._doc)
        self.assertTrue(e._doc is not None)
        self.assertEqual(e.id, existing.id)
        self.assertEqual(e.type_path, existing.type_path)

    def test_latest_value_are_stored_in_entity(self):
        data_record = [('meds', 30),
                       ('doc', "asif"),
                       ('facility', 'clinic'),
                       ('opened_on', datetime(2011, 01, 02, tzinfo=UTC))]
        entity = self.reload_entity(self.test_data.entity1)
        data_record_id = entity.add_data(data=data_record,
                                         event_time=datetime(2011, 01, 02, tzinfo=UTC),
                                         submission=dict(submission_id="123456"))
        self.assertTrue(data_record_id is not None)
        updated_clinic_entity = get_by_short_code(dbm=self.manager, short_code=self.test_data.entity1.short_code,
                                                  entity_type=self.test_data.ENTITY_TYPE)
        self.assertEqual(entity.id, updated_clinic_entity.id)
        self.assertEqual(30, updated_clinic_entity.data['meds']['value'])
        self.assertEqual('asif', updated_clinic_entity.data['doc']['value'])
        self.assertEqual('clinic', updated_clinic_entity.data['facility']['value'])

    def test_invalidate_data(self):
        entity = self.reload_entity(self.test_data.entity1)
        data_record_id = entity.add_data([('arv', 20)])
        valid_doc = DataRecord.get(self.manager, data_record_id)
        self.assertFalse(valid_doc.voided)
        self.test_data.entity1.invalidate_data(data_record_id)
        invalid_doc = DataRecord.get(self.manager, data_record_id)
        self.assertTrue(invalid_doc.voided)

    def test_all_data_record_are_invalidated_when_entity_is_invalidated(self):
        e = Entity(self.manager, entity_type='store', location=['nyc'])
        e.save()
        self.assertFalse(e._doc.void)
        data = [
            [('apples', 20), ('oranges', 30)],
            [('apples', 10), ('oranges', 20)]
        ]
        data_ids = []
        for d in data:
            id = e.add_data(d)
            self.assertFalse(self.manager._load_document(id).void)
            data_ids.append(id)
        e.invalidate()
        self.assertTrue(e._doc.void)
        for id in data_ids:
            self.assertTrue(self.manager._load_document(id).void)

    def test_latest_values_for_entity(self):
        test_data = self.test_data
        entity = self.reload_entity(test_data.entity1)
        entity.add_data(
            data=[("beds", 10), ("meds", 20),
                  ("doctors", 2)])
        entity.add_data(
            data=[("beds", 15), ("doctors", 2)])
        entity.add_data(
            data=[("beds", 20), ("meds", 05),
                  ("doctors", 2)])

        data_fetched = entity.latest_values()
        self.assertEqual(data_fetched["beds"], 20)
        self.assertEqual(data_fetched["meds"], 05)
        self.assertEqual(data_fetched["doctors"], 2)

    def test_should_update_entity_with_location_and_geometry(self):
        short_code = "rep001"
        entity_type = ["reporter"]
        entity = Entity(self.manager, entity_type=entity_type, location=["India", "MH", "Pune"], short_code=short_code)
        self.assertEqual(entity.location_path, ["India", "MH", "Pune"])
        new_location = ["Canada", "Calgary"]
        geometry = None
        entity.set_location_and_geo_code(new_location, geometry)
        self.assertFalse(entity.location_path == ["India", "MH", "Pune"])
        self.assertTrue(entity.location_path == ["Canada", "Calgary"])

    def test_should_get_by_short_code_include_voided_ignore_short_code_case(self):
        with patch("mangrove.datastore.entity._entity_by_short_code") as _entity_by_short_code:
            _entity_by_short_code.return_value = Mock(spec=Entity)
            get_by_short_code_include_voided(self.manager, "SHORT_CODE_IN_UPPER_CASE", ["reporter"])

            _entity_by_short_code.assert_called_once_with(self.manager, "short_code_in_upper_case", ["reporter"])

    def test_should_get_by_short_code_ignore_short_code_case(self):
        with patch("mangrove.datastore.entity.by_short_code") as by_short_code:
            by_short_code.return_value = Mock(spec=Entity)
            get_by_short_code(self.manager, "SHORT_CODE_IN_UPPER_CASE", ["reporter"])

            by_short_code.assert_called_once_with(self.manager, "short_code_in_upper_case", ["reporter"])

    def test_should_know_whether_the_entity_is_a_reporter(self):
        short_code = "rep001"
        entity_type = ["reporter"]
        entity = Entity(self.manager, entity_type=entity_type, location=["India", "MH", "Pune"], short_code=short_code)

        self.assertTrue(entity.is_reporter)


def get_entities(dbm, ids):
    return dbm.get_many(ids, Entity)

# Adaptor methods to old api
def get(dbm, id):
    return dbm.get(id, Entity)


if __name__ == '__main__':
    unittest.main()