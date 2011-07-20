# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
import unittest
from unittest.case import SkipTest
from datawinners.main.initial_couch_fixtures import create_data_dict
from mangrove.datastore.data import EntityAggregration
from mangrove.datastore.database import  get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.entity import Entity
from mangrove.datastore import data


@SkipTest
class TestViewPerf(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        self.meds_type = create_data_dict(dbm=self.dbm, name='Medicines', slug='meds', primitive_type='number',
                                          description='Number of medications')
        self.beds_type = create_data_dict(dbm=self.dbm, name='Beds', slug='beds', primitive_type='number',
                                          description='Number of beds')
        self.director_type = create_data_dict(dbm=self.dbm, name='Director', slug='dir', primitive_type='string',
                                              description='Name of director')
        self.patients_type = create_data_dict(dbm=self.dbm, name='Patients', slug='patients', primitive_type='number',
                                              description='Patient Count')

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def test_should_create_with_bulk_upload(self):
        NUM_ENTITIES = 1000
        DATA_REC_PER_ENTITY = 10
        BATCH = (NUM_ENTITIES * DATA_REC_PER_ENTITY) / 1

        start = datetime.datetime.now()
        le = [Entity(self.dbm, entity_type=["Health_Facility", "Clinic"], location=['India', 'MH', 'Pune'])
              for x in range(0,
                             NUM_ENTITIES)]
        entity_docs = [x._doc for x in le]
        r = self.dbm.database.update(entity_docs)
        end = datetime.datetime.now()
        print "Updating entities took %s" % (end - start,)

        print "data records"
        for e in le:
            for i in range(0, DATA_REC_PER_ENTITY):
                e.add_data_bulk(data=[("beds", 10, self.beds_type), ("meds", 10, self.meds_type)])

        print "total bulk docs %s" % (len(self.dbm.bulk))
        print "bulk save !"

        start = datetime.datetime.now()

        for s in range(0, len(self.dbm.bulk))[::BATCH]:
            start = datetime.datetime.now()
            r = self.dbm.database.update(self.dbm.bulk[s:s + BATCH])
            end = datetime.datetime.now()

        print "Bulk updates took %s" % (end - start,)

        print "Firing view..."
        start = datetime.datetime.now()
        values = data.aggregate(self.dbm, entity_type=["Health_Facility", "Clinic"],
                                aggregates={"beds": data.reduce_functions.LATEST,
                                            "meds": data.reduce_functions.COUNT}, aggregate_on=EntityAggregration()
        )
        end = datetime.datetime.now()
        print "views took %s" % (end - start,)
        print "Done!"
