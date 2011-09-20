# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from mangrove.datastore.entity import Entity, get_by_short_code
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.documents import DataRecordDocument
from mangrove.datastore.datadict import DataDictType
from pytz import UTC
import unittest


# Adaptor methods to old api
def get(dbm, id):
    return dbm.get(id, Entity)


class TestDataStoreApi(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        e = Entity(self.dbm, entity_type="clinic", location=["India", "MH", "Pune"])
        self.uuid = e.save()

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)



    def test_latest_value_are_stored_in_entity(self):
        clinic_entity, clinic_shortcode, reporter_entity, reporter_entity_short_code = self._create_clinic_and_reporter()
        doctor_type, facility_type, med_type, opened_type = self._create_data_dict_type()
        data_record = [('meds', 30, med_type),
            ('doc', "asif", doctor_type),
            ('facility', 'clinic', facility_type),
            ('opened_on', datetime(2011, 01, 02, tzinfo=UTC), opened_type)]
        data_record_id = clinic_entity.add_data(data=data_record,
                                                event_time=datetime(2011, 01, 02, tzinfo=UTC),
                                                submission=dict(submission_id="123456"))
        self.assertTrue(data_record_id is not None)
        updated_clinic_entity = get_by_short_code(dbm=self.dbm, short_code=clinic_shortcode,
                                                  entity_type=['clinic'])
        self.assertEqual(30, updated_clinic_entity.data['meds']['value'])
        self.assertEqual('asif', updated_clinic_entity.data['doc']['value'])
        self.assertEqual('clinic', updated_clinic_entity.data['facility']['value'])


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
        apple_type.save()
        orange_type.save()
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
        reporter = Entity(self.dbm, entity_type="Reporter", location=["Pune", "India"], short_code="REP999")
        self.assertEqual(reporter.short_code, "REP999")


    def _create_data_dict_type(self):
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
        return doctor_type, facility_type, med_type, opened_type

    def _create_clinic_and_reporter(self):
        clinic_entity_short_code = 'clinic01'
        clinic_entity = Entity(self.dbm, entity_type="clinic",
                               location=["India", "MH", "Pune"], short_code=clinic_entity_short_code)
        clinic_entity.save()
        reporter_entity_short_code = 'reporter01'
        reporter_entity = Entity(self.dbm, entity_type="reporter", short_code=reporter_entity_short_code)
        reporter_entity.save()
        return clinic_entity, clinic_entity_short_code, reporter_entity, reporter_entity_short_code


def get_entities(dbm, ids):
    return dbm.get_many(ids, Entity)
