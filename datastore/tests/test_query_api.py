import datetime
from mangrove.datastore.aggregrate import aggregate_by_form_code_python, Sum, Min, Max
from mangrove.datastore.data import  LocationAggregration, LocationFilter, EntityAggregration, TypeAggregration, aggregate_for_form
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
import unittest
from pytz import UTC
from mangrove.datastore.entity import Entity, get_all_entity_types, define_type, get_entities_by_value
from mangrove.datastore import data
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import FormModel


class TestQueryApi(unittest.TestCase):
    def setUp(self):
        self.manager = get_db_manager('http://localhost:5984/', 'mangrove-test')

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.manager)

    def create_reporter(self):
        r = Entity(self.manager, entity_type=["Reporter"])
        r.save()
        return r

    def create_datadict_types(self):
        dd_types = {
            'beds': DataDictType(self.manager, name='beds', slug='beds', primitive_type='number'),
            'meds': DataDictType(self.manager, name='meds', slug='meds', primitive_type='number'),
            'patients': DataDictType(self.manager, name='patients', slug='patients', primitive_type='number'),
            'doctors': DataDictType(self.manager, name='doctors', slug='doctors', primitive_type='number'),
            'director': DataDictType(self.manager, name='director', slug='director', primitive_type='string')
        }
        for label, dd_type in dd_types.items():
            dd_type.save()
        return dd_types

    def test_can_create_views(self):
        # TODO: this test should not just pick two random views... for example entity_types is not used anywhere
        #self.assertTrue(views.exists_view("by_values", self.manager))
        #self.assertTrue(views.exists_view("entity_types", self.manager))
        pass

    def test_should_get_current_values_for_entity(self):
        dd_types = self.create_datadict_types()
        e = Entity(self.manager, entity_type=["Health_Facility.Clinic"], location=['India', 'MH', 'Pune'])
        e.save()
        e.add_data(
            data=[("beds", 10, dd_types['beds']), ("meds", 20, dd_types['meds']), ("doctors", 2, dd_types['doctors'])],
            event_time=datetime.datetime(2011, 01, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 15, dd_types['beds']), ("doctors", 2, dd_types['doctors'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(
            data=[("beds", 20, dd_types['beds']), ("meds", 05, dd_types['meds']), ("doctors", 2, dd_types['doctors'])],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        # values asof
        data_fetched = e.values({"beds": "latest", "meds": "latest", "doctors": "latest"},
                                                                                         asof=datetime.datetime(2011, 01
                                                                                                                , 31,
                                                                                                                tzinfo=UTC))
        self.assertEqual(data_fetched["beds"], 10)
        self.assertEqual(data_fetched["meds"], 20)
        self.assertEqual(data_fetched["doctors"], 2)

        # values asof
        data_fetched = e.values({"beds": "latest", "meds": "latest", "doctors": "latest"},
                                                                                         asof=datetime.datetime(2011, 03
                                                                                                                , 2,
                                                                                                                tzinfo=UTC))
        self.assertEqual(data_fetched["beds"], 20)
        self.assertEqual(data_fetched["meds"], 5)
        self.assertEqual(data_fetched["doctors"], 2)

        # current values
        data_fetched = e.values({"beds": "latest", "meds": "latest", "doctors": "latest"})
        self.assertEqual(data_fetched["beds"], 20)
        self.assertEqual(data_fetched["meds"], 5)
        self.assertEqual(data_fetched["doctors"], 2)

    def test_should_fetch_count_per_entity(self):
        dd_types = self.create_datadict_types()
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        e.save()
        e.add_data(data=[("beds", 300, dd_types['beds']), ("meds", 20, dd_types['meds']),\
                ("director", "Dr. A", dd_types['director']), ("patients", 10, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("meds", 20, dd_types['meds']), ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 250, dd_types['meds']),\
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 400, dd_types['meds']),\
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))
        #        values = data.fetch(self.manager, entity_type=ENTITY_TYPE,
        #                            aggregates={"beds": data.reduce_functions.COUNT,
        #                                        "patients": data.reduce_functions.COUNT},
        #                            aggregate_on={'type': 'location', "level": 2})
        values = data.aggregate(self.manager, entity_type=ENTITY_TYPE,
                                          aggregates={"beds": data.reduce_functions.COUNT,
                                                      "patients": data.reduce_functions.COUNT},
                                          aggregate_on=LocationAggregration(level=2))
        self.assertEqual(len(values), 2)
        self.assertEqual(values[("India", "MH")], {"beds": 1, "patients": 2})

    def test_should_fetch_aggregate_per_entity(self):
        # Aggregate across all data records for each entity

        # Setup: Create clinic entities
        dd_types = self.create_datadict_types()
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        id1 = e.save()
        e.add_data(data=[("beds", 300, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("director", "Dr. A", dd_types['director']), ("patients", 10, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 500, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        id2 = e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 250, dd_types['meds']),
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 400, dd_types['meds']),
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Mumbai'])
        id3 = e.save()
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 50, dd_types['meds']),
                ("director", "Dr. C", dd_types['director']), ("patients", 12, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        values = data.aggregate(self.manager, entity_type=ENTITY_TYPE,
                                          aggregates={"director": data.reduce_functions.LATEST,
                                                      "beds": data.reduce_functions.LATEST,
                                                      "patients": data.reduce_functions.SUM},
                                          aggregate_on=EntityAggregration())

        self.assertEqual(len(values), 3)
        self.assertEqual(values[id1], {"director": "Dr. A", "beds": 500, "patients": 30})
        self.assertEqual(values[id2], {"director": "Dr. B2", "beds": 200, "patients": 70})
        self.assertEqual(values[id3], {"director": "Dr. C", "beds": 200, "patients": 12})

    #        START_TIME = datetime.datetime(2011,01,01, tzinfo = UTC)
    #        END_TIME = datetime.datetime(2011,02,28, tzinfo = UTC)
    #        values = data.fetch(self.manager,entity_type=ENTITY_TYPE,
    #                            aggregates = {  "director" : "latest" ,
    #                                             "beds" : "latest" ,
    #                                             "patients" : "sum"  },
    #                            filter = { "time" : dict(start=START_TIME,end=END_TIME)}
    #                            )
    #        self.assertEqual(len(values),3)
    #        self.assertEqual(values[id1],{ "director" : "Dr. A", "beds" : 300, "patients" : 10})
    #        self.assertEqual(values[id2],{ "director" : "Dr. B1", "beds" : 100, "patients" : 50})
    #        self.assertEqual(values[id3],{ "director" : "Dr. C", "beds" : 200, "patients" : 12})

    def test_should_filter_aggregate_per_entity_for_a_location(self):
        dd_types = self.create_datadict_types()
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        FEB = datetime.datetime(2011, 02, 01, tzinfo=UTC)
        MARCH = datetime.datetime(2011, 03, 01, tzinfo=UTC)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        id1_pune = e.save()

        e.add_data(data=[("beds", 300, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("director", "Dr. A", dd_types['director']), ("patients", 10, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 500, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 20, dd_types['patients'])],
                   event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        id2_pune = e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 10, dd_types['meds']),
                ("director", "Dr. AA", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 20, dd_types['patients'])],
                   event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        id3_pune = e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 10, dd_types['meds']),
                ("director", "Dr. AAA", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 50, dd_types['patients'])],
                   event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 250, dd_types['meds']),
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 400, dd_types['meds']),
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Mumbai'])
        e.save()
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 50, dd_types['meds']),
                ("director", "Dr. C", dd_types['director']), ("patients", 12, dd_types['patients'])],
                   event_time=MARCH)

        #        values = data.fetch(self.manager, entity_type=ENTITY_TYPE,
        #                            aggregates={"director": data.reduce_functions.LATEST,
        #                                        "beds": data.reduce_functions.LATEST,
        #                                        "patients": data.reduce_functions.SUM},
        #                            filter={'location': ['India', 'MH', 'Pune']}
        #        )
        values = data.aggregate(self.manager, entity_type=ENTITY_TYPE, aggregate_on=EntityAggregration(),
                                          aggregates={"director": data.reduce_functions.LATEST,
                                                      "beds": data.reduce_functions.LATEST,
                                                      "patients": data.reduce_functions.SUM},
                                          filter=LocationFilter(['India', 'MH', 'Pune']))

        self.assertEqual(len(values), 3)
        self.assertEqual(values[id1_pune], {"director": "Dr. A", "beds": 500, "patients": 30})
        self.assertEqual(values[id2_pune], {"director": "Dr. AA", "beds": 200, "patients": 70})
        self.assertEqual(values[id3_pune], {"director": "Dr. AAA", "beds": 200, "patients": 100})

    def test_should_fetch_aggregate_grouped_by_hierarchy_path_for_location(self):
        dd_types = self.create_datadict_types()
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        FEB = datetime.datetime(2011, 02, 01, tzinfo=UTC)
        MARCH = datetime.datetime(2011, 03, 01, tzinfo=UTC)

        # Entities for State 1: Maharashtra
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        e.save()

        e.add_data(data=[("beds", 300, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("director", "Dr. A", dd_types['director']), ("patients", 10, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 500, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 20, dd_types['patients'])],
                   event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 10, dd_types['meds']),
                ("director", "Dr. AA", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 20, dd_types['patients'])],
                   event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Mumbai'])
        e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 10, dd_types['meds']),
                ("director", "Dr. AAA", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 50, dd_types['patients'])],
                   event_time=MARCH)

        # Entities for State 2: karnataka
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 250, dd_types['meds']),
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 400, dd_types['meds']),
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=MARCH)
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Hubli'])
        e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 250, dd_types['meds']),
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 400, dd_types['meds']),
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=MARCH)
        # Entities for State 3: Kerala
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Kerala', 'Kochi'])
        e.save()
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 50, dd_types['meds']),
                ("director", "Dr. C", dd_types['director']), ("patients", 12, dd_types['patients'])],
                   event_time=MARCH)

        values = data.aggregate(self.manager, entity_type=ENTITY_TYPE,
                                          aggregates={"patients": data.reduce_functions.SUM},
                                          aggregate_on=LocationAggregration(level=2),
                                          )
        #        values = data.fetch(self.manager, entity_type=ENTITY_TYPE,
        #                            aggregates={"patients": data.reduce_functions.SUM},
        #                            aggregate_on={'type': 'location', "level": 2},
        #                            )

        self.assertEqual(len(values), 3)
        self.assertEqual(values[("India", "MH")], {"patients": 200})
        self.assertEqual(values[("India", "Karnataka")], {"patients": 140})
        self.assertEqual(values[("India", "Kerala")], {"patients": 12})

        values = data.aggregate(self.manager, entity_type=ENTITY_TYPE,
                                          aggregates={"patients": data.reduce_functions.SUM},
                                          aggregate_on=LocationAggregration(level=2),
                                          filter=LocationFilter(['India', 'MH'])
        )
        #        values = data.fetch(self.manager, entity_type=ENTITY_TYPE,
        #                            aggregates={"patients": data.reduce_functions.SUM},
        #                            aggregate_on={'type': 'location', "level": 2},
        #                            filter={'location': ['India', 'MH']}
        #        )

        self.assertEqual(len(values), 1)
        self.assertEqual(values[("India", "MH")], {"patients": 200})


    def test_should_fetch_aggregate_grouped_by_hierarchy_path_for_any(self):
        dd_types = self.create_datadict_types()
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        FEB = datetime.datetime(2011, 02, 01, tzinfo=UTC)
        MARCH = datetime.datetime(2011, 03, 01, tzinfo=UTC)

        # Entities for State 1: Maharashtra
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        e.set_aggregation_path("governance", ["Director", "Med_Officer", "Surgeon"])
        e.save()

        e.add_data(data=[("beds", 300, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("director", "Dr. A", dd_types['director']), ("patients", 10, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 500, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 20, dd_types['patients'])],
                   event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        e.set_aggregation_path("governance", ["Director", "Med_Supervisor", "Surgeon"])
        e.save()

        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 10, dd_types['meds']),
                ("director", "Dr. AA", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 20, dd_types['patients'])],
                   event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Mumbai'])
        e.set_aggregation_path("governance", ["Director", "Med_Officer", "Doctor"])
        e.save()

        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 10, dd_types['meds']),
                ("director", "Dr. AAA", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 50, dd_types['patients'])],
                   event_time=MARCH)

        # Entities for State 2: karnataka
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        e.set_aggregation_path("governance", ["Director", "Med_Supervisor", "Nurse"])
        e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 250, dd_types['meds']),
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 400, dd_types['meds']),
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=MARCH)
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Hubli'])
        e.set_aggregation_path("governance", ["Director", "Med_Officer", "Surgeon"])
        e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 250, dd_types['meds']),
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=FEB)
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 400, dd_types['meds']),
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=MARCH)

        # Entities for State 3: Kerala
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Kerala', 'Kochi'])
        e.set_aggregation_path("governance", ["Director", "Med_Officer", "Nurse"])
        e.save()
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 50, dd_types['meds']),
                ("director", "Dr. C", dd_types['director']), ("patients", 12, dd_types['patients'])],
                   event_time=MARCH)
        values = data.aggregate(self.manager, entity_type=ENTITY_TYPE,
                                          aggregates={"patients": data.reduce_functions.SUM},
                                          aggregate_on=TypeAggregration(type='governance', level=2)
        )
        #        values = data.fetch(self.manager, entity_type=ENTITY_TYPE,
        #                            aggregates={"patients": data.reduce_functions.SUM},
        #                            aggregate_on={'type': 'governance', "level": 2},
        #                            )

        self.assertEqual(len(values), 2)
        self.assertEqual(values[("Director", "Med_Officer")], {"patients": 212})
        self.assertEqual(values[("Director", "Med_Supervisor")], {"patients": 140})

        values = data.aggregate(self.manager, entity_type=ENTITY_TYPE,
                                          aggregates={"patients": data.reduce_functions.SUM},
                                          aggregate_on=TypeAggregration(type='governance', level=3),
                                          )
        #        values = data.fetch(self.manager, entity_type=ENTITY_TYPE,
        #                            aggregates={"patients": data.reduce_functions.SUM},
        #                            aggregate_on={'type': 'governance', "level": 3},
        #                            )

        self.assertEqual(len(values), 5)
        self.assertEqual(values[("Director", "Med_Officer", "Surgeon")], {"patients": 100})
        self.assertEqual(values[("Director", "Med_Officer", "Doctor")], {"patients": 100})
        self.assertEqual(values[("Director", "Med_Officer", "Nurse")], {"patients": 12})
        self.assertEqual(values[("Director", "Med_Supervisor", "Surgeon")], {"patients": 70})

    def test_should_load_all_entity_types(self):
        define_type(self.manager, ["HealthFacility", "Clinic"])
        define_type(self.manager, ["HealthFacility", "Hospital"])
        define_type(self.manager, ["WaterPoint", "Lake"])
        define_type(self.manager, ["WaterPoint", "Dam"])
        entity_types = get_all_entity_types(self.manager)

        expected = [['HealthFacility'],
            ['HealthFacility', 'Clinic'],
            ['HealthFacility', 'Hospital'],
            ['WaterPoint'],
            ['WaterPoint', 'Lake'],
            ['WaterPoint', 'Dam']]

        for e in expected:
            self.assertIn(e, entity_types)

    def test_should_fetch_aggregate_per_entity_for_all_fields_in_entity(self):
        # Aggregate across all data records for each entity for all fields

        # Setup: Create clinic entities
        dd_types = self.create_datadict_types()
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        id1 = e.save()
        e.add_data(data=[("beds", 300, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("director", "Dr. A", dd_types['director']), ("patients", 10, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 500, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        id2 = e.save()
        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 250, dd_types['meds']),
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 400, dd_types['meds']),
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Mumbai'])
        id3 = e.save()
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 50, dd_types['meds']),
                ("director", "Dr. C", dd_types['director']), ("patients", 12, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        #        values = data.fetch(self.manager, entity_type=ENTITY_TYPE, aggregates={"*": data.reduce_functions.LATEST})
        values = data.aggregate(self.manager, entity_type=ENTITY_TYPE,
                                          aggregates={"*": data.reduce_functions.LATEST},
                                          aggregate_on=EntityAggregration())

        self.assertEqual(len(values), 3)
        self.assertEqual(values[id1], {"director": "Dr. A", "beds": 500, "patients": 20, "meds": 20})
        self.assertEqual(values[id2], {"director": "Dr. B2", "beds": 200, "patients": 20, "meds": 400})
        self.assertEqual(values[id3], {"director": "Dr. C", "beds": 200, "patients": 12, "meds": 50})

    def test_get_entities_by_value(self):
        med_type = DataDictType(self.manager,
                                name='Medicines',
                                slug='meds',
                                primitive_type='number',
                                description='Number of medications',
                                tags=['med'])
        med_type.save()
        doctor_type = DataDictType(self.manager,
                                   name='Doctor',
                                   slug='doc',
                                   primitive_type='string',
                                   description='Name of doctor',
                                   tags=['doctor', 'med'])
        doctor_type.save()
        facility_type = DataDictType(self.manager,
                                     name='Facility',
                                     slug='facility',
                                     primitive_type='string',
                                     description='Name of facility')
        facility_type.save()

        jan = datetime.datetime(2011, 01, 01, tzinfo=UTC)
        feb = datetime.datetime(2011, 02, 01, tzinfo=UTC)
        march = datetime.datetime(2011, 03, 01, tzinfo=UTC)
        april = datetime.datetime(2011, 04, 01, tzinfo=UTC)
        may = datetime.datetime(2011, 05, 03, tzinfo=UTC)

        e = Entity(self.manager, entity_type='foo')
        e.save()
        data_record = [('meds', 20, med_type),
                ('doc', "aroj", doctor_type),
                ('facility', 'clinic', facility_type)]
        e.add_data(data_record, event_time=feb)

        f = Entity(self.manager, entity_type='bar')
        f.save()
        data_record = [('meds', 10, med_type),
                ('doc', "aroj", doctor_type),
                ('facility', 'clinic', facility_type)]
        f.add_data(data_record, event_time=jan)
        data_record = [('foo', 20, med_type),
                ('doc', "aroj", doctor_type),
                ('facility', 'clinic', facility_type)]
        f.add_data(data_record, event_time=march)
        data_record = [('bar', 30, med_type),
                ('doc', "aroj", doctor_type),
                ('facility', 'clinic', facility_type)]
        f.add_data(data_record, event_time=april)

        # datadict_type, no as_of
        entity_ids = [x.id for x in get_entities_by_value(self.manager, med_type, 20)]
        self.assertTrue(e.id in entity_ids)
        self.assertTrue(f.id not in entity_ids)
        # label, no as_of
        entity_ids = [x.id for x in get_entities_by_value(self.manager, 'foo', 20)]
        self.assertTrue(e.id not in entity_ids)
        self.assertTrue(f.id in entity_ids)
        # datadict_type, with as_of
        entity_ids = [x.id for x in get_entities_by_value(self.manager, med_type, 10, as_of=feb)]
        self.assertTrue(e.id not in entity_ids)
        self.assertTrue(f.id in entity_ids)
        # label, with as_of
        entity_ids = [x.id for x in get_entities_by_value(self.manager, 'bar', 30, as_of=may)]
        self.assertTrue(e.id not in entity_ids)
        self.assertTrue(f.id in entity_ids)
        # TODO: more tests for different types?


    def test_should_aggregate_per_entity_per_form_model(self):
        ENTITY_TYPE = ["HealthFacility", "Clinic"]
        self.create_clinic_type(ENTITY_TYPE)
        self._create_form_model("CL2")
        self._create_form_model("CL1")
        dd_types = self.create_datadict_types()
        e, id1 = self.create_entity_instance(ENTITY_TYPE, ['India', 'MH', 'Pune'])

        e.add_data(data=[("beds", 300, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("director", "Dr. A", dd_types['director']), ("patients", 10, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='1', form_code='CL1'))
        e.add_data(data=[("beds", 500, dd_types['beds']), ("meds", 50, dd_types['meds']),
                ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='2', form_code='CL1'))

        e.add_data(data=[("beds", 300, dd_types['beds']), ("doctors", 20, dd_types['doctors']),
                ("director", "Dr. A", dd_types['director']), ("patients", 10, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='1', form_code='CL2'))

        e.add_data(data=[("beds", 200, dd_types['beds']), ("doctors", 10, dd_types['doctors']),
                ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='2', form_code='CL2'))

        e, id2 = self.create_entity_instance(ENTITY_TYPE, ['India', 'Karnataka', 'Bangalore'])

        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 250, dd_types['meds']),
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code='CL1'))
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 400, dd_types['meds']),
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code='CL1'))

        e.add_data(data=[("beds", 150, dd_types['beds']), ("doctors", 50, dd_types['doctors']),
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code='CL2'))
        e.add_data(data=[("beds", 270, dd_types['beds']), ("doctors", 40, dd_types['doctors']),
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code='CL2'))

        e, id3 = self.create_entity_instance(ENTITY_TYPE, ['India', 'MH', 'Mumbai'])
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 50, dd_types['meds']),
                ("director", "Dr. C", dd_types['director']), ("patients", 12, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='5', form_code='CL1'))

        values = aggregate_for_form(dbm=self.manager, form_code='CL1', aggregate_on=EntityAggregration(),
                                        aggregates={"director": data.reduce_functions.LATEST,
                                                    "beds": data.reduce_functions.LATEST,
                                                    "patients": data.reduce_functions.SUM,
                                                    'meds': data.reduce_functions.MIN})

        self.assertEqual(len(values), 3)
        self.assertEqual(values[id1], {"director": "Dr. A", "beds": 500, "patients": 30, 'meds': 20})
        self.assertEqual(values[id2], {"director": "Dr. B2", "beds": 200, "patients": 70, 'meds': 250})
        self.assertEqual(values[id3], {"director": "Dr. C", "beds": 200, "patients": 12, 'meds': 50})

        values = data.aggregate_for_form(dbm=self.manager, form_code='CL2', aggregate_on=EntityAggregration(),
                                             aggregates={"doctors": data.reduce_functions.MAX,
                                                         "beds": data.reduce_functions.SUM,
                                                         'patients': data.reduce_functions.AVG})

        self.assertEqual(len(values), 2)
        self.assertEqual(values[id1], {"doctors": 20, "beds": 500, 'patients': 15})
        self.assertEqual(values[id2], {'doctors': 50, "beds": 420, 'patients': 35})

    def test_should_aggregate_per_entity_per_form_model_with_time_filter(self):
        ENTITY_TYPE = ["HealthFacility", "Clinic"]
        self.create_clinic_type(ENTITY_TYPE)
        self._create_form_model("CL2")
        self._create_form_model("CL1")
        dd_types = self.create_datadict_types()
        e, id1 = self.create_entity_instance(ENTITY_TYPE, ['India', 'MH', 'Pune'])

        e.add_data(data=[("beds", 300, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("director", "Dr. A", dd_types['director']), ("patients", 10, dd_types['patients'])],
                   event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='1', form_code='CL1'))
        e.add_data(data=[("beds", 500, dd_types['beds']), ("meds", 50, dd_types['meds']),
                ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2010, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='2', form_code='CL1'))

        e.add_data(data=[("beds", 300, dd_types['beds']), ("doctors", 20, dd_types['doctors']),
                ("director", "Dr. A", dd_types['director']), ("patients", 10, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='1', form_code='CL1'))

        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 10, dd_types['meds']),
                ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='2', form_code='CL1'))

        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 20, dd_types['meds']),
                ("patients", 45, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 04, 01, tzinfo=UTC),
                   submission=dict(submission_id='2', form_code='CL2'))

        e, id2 = self.create_entity_instance(ENTITY_TYPE, ['India', 'Karnataka', 'Bangalore'])

        e.add_data(data=[("beds", 100, dd_types['beds']), ("meds", 250, dd_types['meds']),
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code='CL1'))
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 400, dd_types['meds']),
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2010, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code='CL1'))

        e.add_data(data=[("beds", 150, dd_types['beds']), ("meds", 50, dd_types['meds']),
                ("director", "Dr. B1", dd_types['director']), ("patients", 50, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code='CL1'))
        e.add_data(data=[("beds", 270, dd_types['beds']), ("doctors", 40, dd_types['doctors']),
                ("director", "Dr. B2", dd_types['director']), ("patients", 20, dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code='CL2'))

        e, id3 = self.create_entity_instance(ENTITY_TYPE, ['India', 'MH', 'Mumbai'])
        e.add_data(data=[("beds", 200, dd_types['beds']), ("meds", 50, dd_types['meds']),
                ("director", "Dr. C", dd_types['director']), ("patients", 12, dd_types['patients'])],
                   event_time=datetime.datetime(2010, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='5', form_code='CL1'))

        values = aggregate_by_form_code_python(dbm=self.manager, form_code='CL1',
                                               aggregate_on=EntityAggregration(),
                                               aggregates=[Sum("patients"), Min('meds'), Max('beds')],
                                               starttime="01-01-2011 00:00:00", endtime="31-12-2011 00:00:00")
        #        values = aggregate_by_form_code_with_time_filter(dbm=self.manager, form_code='CL1', aggregate_on=EntityAggregration(),
        #                                             aggregates={"director": data.reduce_functions.LATEST,
        #                                                         "beds": data.reduce_functions.LATEST,
        #                                                         "patients": data.reduce_functions.SUM,
        #                                                         'meds': data.reduce_functions.MIN})

        self.assertEqual(len(values), 2)
        self.assertEqual(values[id1], {"patients": 30, 'meds': 10, 'beds': 300})
        self.assertEqual(values[id2], {"patients": 50, 'meds': 50, 'beds': 150})

    #        self.assertEqual(values[id3], {"patients": 12, 'meds': 50})
    #        values = aggregate_by_form_code_python(dbm=self.manager, form_code='CL1',
    #                                                         aggregate_on=EntityAggregration(),
    #                                                         aggregates=[Sum("patients"), Min('meds')],
    #                                                         starttime="")

    #        self.assertEqual(values[id1], {"director": "Dr. A", "beds": 500, "patients": 30, 'meds': 20})
    #        self.assertEqual(values[id2], {"director": "Dr. B2", "beds": 200, "patients": 70, 'meds': 250})
    #        self.assertEqual(values[id3], {"director": "Dr. C", "beds": 200, "patients": 12, 'meds': 50})

    #        values = data.aggregate_by_form_code(dbm=self.manager, form_code='CL2', aggregate_on=EntityAggregration(),
    #                                             aggregates={"doctors": data.reduce_functions.MAX,
    #                                                         "beds": data.reduce_functions.SUM,
    #                                                         'patients': data.reduce_functions.AVG})
    #
    #        self.assertEqual(len(values), 2)
    #        self.assertEqual(values[id1], {"doctors": 20, "beds": 500, 'patients': 15})
    #        self.assertEqual(values[id2], {'doctors': 50, "beds": 420, 'patients': 35})


    def create_entity_instance(self, ENTITY_TYPE, location):
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=location)
        id1 = e.save()
        return e, id1

    def create_clinic_type(self, entity_type):
        self.entity_type = entity_type
        define_type(self.manager, entity_type)


    def _create_form_model(self, form_code):
        self.default_ddtype = DataDictType(self.manager, name='Default String Datadict Type', slug='string_default',
                                           primitive_type='string')
        self.default_ddtype.save()
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=self.default_ddtype)
        question2 = TextField(name="question1_Name", code="Q1", label="What is your name",
                              defaultValue="some default value", language="eng",
                              ddtype=self.default_ddtype)
        question3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age",
                                 ddtype=self.default_ddtype)
        question4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
                                options=[("RED", 1), ("YELLOW", 2)], ddtype=self.default_ddtype)

        self.form_model = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                    form_code=form_code, type='survey', fields=[
                question1, question2, question3, question4])
        self.form_model__id = self.form_model.save()
