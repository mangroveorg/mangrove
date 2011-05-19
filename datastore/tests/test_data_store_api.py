# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from mock import Mock
from mangrove.datastore.entity import Entity, define_type, get_all_entity_types, generate_entity_short_code, _get_used_short_codes
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager, DatabaseManager
from mangrove.datastore.documents import DataRecordDocument
from mangrove.datastore.datadict import DataDictType
from pytz import UTC
import unittest
from mangrove.errors.MangroveException import EntityTypeAlreadyDefined, ShortCodeAlreadyInUseException


# Adaptor methods to old api
from mangrove.utils.types import is_empty

def get(dbm, id):
    return dbm.get(id, Entity)


def get_entities(dbm, ids):
    return dbm.get_many(ids, Entity)


class TestDataStoreApi(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        e = Entity(self.dbm, entity_type="clinic", location=["India", "MH", "Pune"])
        self.uuid = e.save()

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
        e = get(self.dbm, self.uuid)
        self.assertTrue(e.id)
        self.assertTrue(e.type_string == "clinic")

    def test_should_add_location_hierarchy_on_create(self):
        e = Entity(self.dbm, entity_type="clinic", location=["India", "MH", "Pune"])
        uuid = e.save()
        saved = get(self.dbm, uuid)
        self.assertEqual(saved.location_path, ["India", "MH", "Pune"])

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
        self.assertTrue(saved.aggregation_paths["org"] == ["TW", "PS", "IS"])

    def test_save_aggregation_path_only_via_api(self):
        e = get(self.dbm, self.uuid)
        e.location_path[0] = "US"
        e.save()
        saved = get(self.dbm, self.uuid)
        self.assertTrue(saved.location_path == ["India", "MH", "Pune"])  # Hierarchy has not changed.

    def test_should_save_hierarchy_tree_only_through_api(self):
        e = get(self.dbm, self.uuid)
        org_hierarchy = ["TW", "PS", "IS"]
        e.set_aggregation_path("org", org_hierarchy)
        e.save()
        e.aggregation_paths['org'][0] = "XYZ"
        e.save()
        saved = get(self.dbm, self.uuid)
        self.assertEqual(saved.aggregation_paths["org"], ["TW", "PS", "IS"])

    def test_get_entities(self):
        e2 = Entity(self.dbm, "hospital", ["India", "TN", "Chennai"])
        id2 = e2.save()
        entities = get_entities(self.dbm, [self.uuid, id2])
        self.assertEqual(len(entities), 2)
        saved = dict([(e.id, e) for e in entities])
        self.assertEqual(saved[id2].type_string, "hospital")
        self.assertEqual(saved[self.uuid].type_string, "clinic")
        self.dbm.delete(e2)

    def _create_clinic_and_reporter(self):
        clinic_entity = Entity(self.dbm, entity_type="clinic",
                               location=["India", "MH", "Pune"])
        clinic_entity.save()
        reporter_entity = Entity(self.dbm, entity_type="reporter")
        reporter_entity.save()
        return clinic_entity, reporter_entity

    def test_add_data_record_to_entity(self):
        clinic_entity, reporter = self._create_clinic_and_reporter()
        med_type = DataDictType(self.dbm, name='Medicines', slug='meds', primitive_type='number',
                                description='Number of medications')
        doctor_type = DataDictType(self.dbm, name='Doctor', slug='doc', primitive_type='string',
                                   description='Name of doctor')
        facility_type = DataDictType(self.dbm, name='Facility', slug='facility', primitive_type='string',
                                     description='Name of facility')
        opened_type = DataDictType(self.dbm, name='Opened on', slug='opened_on', primitive_type='datetime',
                                   description='Date of opening')
        med_type.save()
        doctor_type.save()
        facility_type.save()
        opened_type.save()
        data_record = [('meds', 20, med_type),
                       ('doc', "aroj", doctor_type),
                       ('facility', 'clinic', facility_type),
                       ('opened_on', datetime(2011, 01, 02, tzinfo=UTC), opened_type)]
        data_record_id = clinic_entity.add_data(data=data_record,
                                                event_time=datetime(2011, 01, 02, tzinfo=UTC),
                                                submission_id="123456")
        self.assertTrue(data_record_id is not None)

        # Assert the saved document structure is as expected
        saved = self.dbm._load_document(data_record_id, document_class=DataRecordDocument)
        for (label, value, dd_type) in data_record:
            self.assertTrue(label in saved.data)
            self.assertTrue('value' in saved.data[label])
            self.assertTrue('type' in saved.data[label])
            self.assertTrue(value == saved.data[label]['value'])
            # TODO: not sure how to test that dd_type == saved.data[label]['type']
            # it seems the following has different representations for datetimes
            #self.assertTrue(dd_type._doc.unwrap() == DataDictDocument(saved.data[label]['type']))
        self.assertEqual(saved.event_time, datetime(2011, 01, 02, tzinfo=UTC))
        self.assertEqual(saved.submission_id, "123456")

    def test_should_create_entity_from_document(self):
        existing = self.dbm.get(self.uuid, Entity)
        e = Entity.new_from_db(self.dbm, existing._doc)
        self.assertTrue(e._doc is not None)
        self.assertEqual(e.id, existing.id)
        self.assertEqual(e.type_path, existing.type_path)

    def test_invalidate_data(self):
        e = Entity(self.dbm, entity_type='store', location=['nyc'])
        e.save()
        apple_type = DataDictType(self.dbm, name='Apples', slug='apples', primitive_type='number')
        orange_type = DataDictType(self.dbm, name='Oranges', slug='oranges', primitive_type='number')
        apple_type.save()
        orange_type.save()
        data = e.add_data([('apples', 20, apple_type), ('oranges', 30, orange_type)])
        valid_doc = self.dbm._load_document(data)
        self.assertFalse(valid_doc.void)
        e.invalidate_data(data)
        invalid_doc = self.dbm._load_document(data)
        self.assertTrue(invalid_doc.void)

    def test_invalidate_entity(self):
        e = Entity(self.dbm, entity_type='store', location=['nyc'])
        e.save()
        self.assertFalse(e._doc.void)
        apple_type = DataDictType(self.dbm, name='Apples', slug='apples', primitive_type='number')
        orange_type = DataDictType(self.dbm, name='Oranges', slug='oranges', primitive_type='number')
        data = [
                [('apples', 20, apple_type), ('oranges', 30, orange_type)],
                [('apples', 10, apple_type), ('oranges', 20, orange_type)]
        ]
        data_ids = []
        for d in data:
            id = e.add_data(d)
            self.assertFalse(self.dbm._load_document(id).void)
            data_ids.append(id)
        e.invalidate()
        self.assertTrue(e._doc.void)
        for id in data_ids:
            self.assertTrue(self.dbm._load_document(id).void)

    def test_should_define_entity_type(self):
        entity_type = ["HealthFacility", "Clinic"]
        entity_types = get_all_entity_types(self.dbm)
        self.assertNotIn(entity_type, entity_types)
        define_type(self.dbm, entity_type)
        types = get_all_entity_types(self.dbm)
        self.assertIn(entity_type, types)
        self.assertIn([entity_type[0]], types)

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

    def test_should_return_data_types(self):
        med_type = DataDictType(self.dbm,
                                name='Medicines',
                                slug='meds',
                                primitive_type='number',
                                description='Number of medications',
                                tags=['med'])
        med_type.save()
        doctor_type = DataDictType(self.dbm,
                                   name='Doctor',
                                   slug='doc',
                                   primitive_type='string',
                                   description='Name of doctor',
                                   tags=['doctor', 'med'])
        doctor_type.save()
        facility_type = DataDictType(self.dbm,
                                     name='Facility',
                                     slug='facility',
                                     primitive_type='string',
                                     description='Name of facility')
        facility_type.save()
        e = Entity(self.dbm, entity_type='foo')
        e.save()
        data_record = [('meds', 20, med_type),
                       ('doc', "aroj", doctor_type),
                       ('facility', 'clinic', facility_type)]
        e.add_data(data_record)
        # med (tag in list)
        types = [typ.slug for typ in e.data_types(['med'])]
        self.assertTrue(med_type.slug in types)
        self.assertTrue(doctor_type.slug in types)
        self.assertTrue(facility_type.slug not in types)
        # doctor (tag as string)
        types = [typ.slug for typ in e.data_types('doctor')]
        self.assertTrue(doctor_type.slug in types)
        self.assertTrue(med_type.slug not in types)
        self.assertTrue(facility_type.slug not in types)
        # med and doctor (more than one tag)
        types = [typ.slug for typ in e.data_types(['med', 'doctor'])]
        self.assertTrue(doctor_type.slug in types)
        self.assertTrue(med_type.slug not in types)
        self.assertTrue(facility_type.slug not in types)
        # no tags
        types = [typ.slug for typ in e.data_types()]
        self.assertTrue(med_type.slug in types)
        self.assertTrue(doctor_type.slug in types)
        self.assertTrue(facility_type.slug in types)

    def test_should_create_entity_with_short_code(self):
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP999")
        self.assertEqual(reporter.short_code, "REP999")


    def test_should_return_all_short_ids_for_given_entity_type(self):
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP0")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP1")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP2")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"])
        reporter.save()
        used_id_dict = _get_used_short_codes(self.dbm, entity_type = "Reporter")
        self.assertTrue("REP2" in used_id_dict["Reporter"])
        self.assertTrue(len(used_id_dict["Reporter"]), 4)

    def test_should_return_only_short_code_specified(self):
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP0")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP1")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP2")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"])
        reporter.save()
        used_id_dict = _get_used_short_codes(self.dbm, entity_type = "Reporter", short_code ='REP2')
        self.assertTrue("REP2" in used_id_dict["Reporter"])
        self.assertEqual(len(used_id_dict.values()), 1)

    def test_should_return_none_if_no_entity_of_type_exists(self):
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP0")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP1")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP2")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"])
        reporter.save()
        used_id_dict = _get_used_short_codes(self.dbm, entity_type = "Clinic", short_code ='CLI1')
        self.assertTrue('CLI1' not in used_id_dict["Clinic"])
        self.assertTrue(is_empty(used_id_dict["Clinic"]))

    def test_should_return_short_codes_for_all_entities_if_entity_not_specified(self):
        _delete_db_and_remove_db_manager(self.dbm)
        self.dbm = get_db_manager(database='mangrove-test')
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP0")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune","India"], short_code="REP1")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="Clinic", location=["Pune","India"], short_code="CLI0")
        reporter.save()
        reporter = Entity(self.dbm, entity_type="School", location=["Pune","India"], short_code="SCH1")
        reporter.save()
        used_id_dict = _get_used_short_codes(self.dbm)
        self.assertEqual(len(used_id_dict.keys()), 3)
        self.assertEqual(len(used_id_dict["Reporter"]), 2)
        self.assertEqual(len(used_id_dict["Clinic"]), 1)
        self.assertEqual(len(used_id_dict["School"]), 1)

    def test_should_return_short_name_if_not_in_list(self):
        manager = Mock(spec=DatabaseManager)
        manager.load_all_rows_in_view = Mock(return_value=[{"key": [["Reporter"], "REP2"], "value":1},
                                                           {"key": [["Reporter"], "REP1"], "value":1},
                                                           {"key": [["Reporter"], "REP0"], "value":1}])
        id = generate_entity_short_code(manager, entity_type="Reporter", suggested_id="REP4")
        assert manager.load_all_rows_in_view.called
        self.assertEqual(id, "REP4")

    def test_should_raise_IdAlreadyInUse_if_suggested_id_used(self):
        with self.assertRaises(ShortCodeAlreadyInUseException) as e:
            manager = Mock(spec=DatabaseManager)
            manager.load_all_rows_in_view = Mock(return_value=[{"key": [["Reporter"], "REP2"], "value":1},
                                                               {"key": [["Reporter"], "REP1"], "value":1},
                                                               {"key": [["Reporter"], "REP0"], "value":1}])
            id = generate_entity_short_code(manager, entity_type="Reporter", suggested_id="REP2")

    def test_should_generate_short_id_and_return_if_suggested_id_is_blank(self):
        manager = Mock(spec=DatabaseManager)
        manager.load_all_rows_in_view = Mock(return_value=[{"key": [["Reporter"], "REP2"], "value":1},
                                                           {"key": [["Reporter"], "REP1"], "value":1},
                                                           {"key": [["Reporter"], "REP0"], "value":1}])
        id = generate_entity_short_code(manager, entity_type="Reporter", suggested_id="")
        assert manager.load_all_rows_in_view.called
        self.assertEqual(id, "REP3")

    def test_should_generate_short_id_and_return_if_suggested_id_is_not_supplied(self):
        manager = Mock(spec=DatabaseManager)
        manager.load_all_rows_in_view = Mock(return_value=[{"key": [["Reporter"], "REP2"], "value":1},
                                                           {"key": [["Reporter"], "REP1"], "value":1},
                                                           {"key": [["Reporter"], "REP0"], "value":1}])
        id = generate_entity_short_code(manager, entity_type="Reporter")
        assert manager.load_all_rows_in_view.called
        self.assertEqual(id, "REP3")

    def test_should_generate_short_code_when_the_entity_type_has_no_instances_amd_no_id_suggested(self):
        manager = Mock(spec=DatabaseManager)
        manager.load_all_rows_in_view = Mock(return_value=[])
        id = generate_entity_short_code(manager, entity_type="Clinic")
        assert manager.load_all_rows_in_view.called
        self.assertEqual(id, "CLI1")





