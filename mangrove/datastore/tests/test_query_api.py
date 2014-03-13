import datetime
import unittest
from mangrove.datastore.aggregrate import aggregate_by_form_code_python, Sum, Min, Max, Latest, aggregation_factory
from mangrove.datastore.data import  LocationAggregration, LocationFilter, EntityAggregration, TypeAggregration, aggregate_for_form
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from pytz import UTC
from mangrove.datastore.entity import Entity, get_entities_by_value, create_entity, entities_exists_with_value
from mangrove.datastore import data
from mangrove.datastore.entity_type import define_type
from mangrove.datastore.tests.test_data import TestData
from mangrove.form_model.field import TextField, IntegerField, SelectField, UniqueIdField
from mangrove.form_model.form_model import FormModel
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase


class TestQueryApi(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)

    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def create_reporter(self):
        r = Entity(self.manager, entity_type=["Reporter"])
        r.save()
        return r

    def test_can_create_views(self):
        # TODO: this test should not just pick two random views... for example entity_types is not used anywhere
        #self.assertTrue(views.exists_view("by_values", self.manager))
        #self.assertTrue(views.exists_view("entity_types", self.manager))
        pass

    def test_should_get_current_values_for_entity(self):
        e = Entity(self.manager, entity_type=["Health_Facility.Clinic"], location=['India', 'MH', 'Pune'])
        e.save()
        e.add_data(
            data=[("beds", 10), ("meds", 20), ("doctors", 2)],
            event_time=datetime.datetime(2011, 01, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 15), ("doctors", 2)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(
            data=[("beds", 20), ("meds", 05), ("doctors", 2)],
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
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        e.save()
        e.add_data(data=[("beds", 300), ("meds", 20),\
                         ("director", "Dr. A"), ("patients", 10)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("meds", 20), ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        e.save()
        e.add_data(data=[("beds", 100), ("meds", 250),\
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 200), ("meds", 400),\
                         ("director", "Dr. B2"), ("patients", 20)],
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
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        id1 = e.save()
        e.add_data(data=[("beds", 300), ("meds", 20),
                         ("director", "Dr. A"), ("patients", 10)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 500), ("meds", 20),
                         ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        id2 = e.save()
        e.add_data(data=[("beds", 100), ("meds", 250),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 200), ("meds", 400),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Mumbai'])
        id3 = e.save()
        e.add_data(data=[("beds", 200), ("meds", 50),
                         ("director", "Dr. C"), ("patients", 12)],
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

    def test_should_fetch_latest_per_entity(self):
        # Aggregate across all data records for each entity

        # Setup: Create clinic entities
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        define_type(self.manager, ENTITY_TYPE)

        # create entity 1 and add datarecord
        clinic01 = 'cl01'
        e = create_entity(self.manager, entity_type=ENTITY_TYPE, short_code=clinic01)
        e.add_data(data=[("beds", 300), ("meds", 20),
                         ("director", "Dr. A"), ("patients", 10)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))

        e.add_data(data=[("beds", 500), ("meds", 20),
                         ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        clinic02 = 'cl02'
        e = create_entity(self.manager, entity_type=ENTITY_TYPE, short_code=clinic02)

        e.add_data(data=[("beds", 100), ("meds", 250),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 200), ("meds", 400),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        clinic03 = 'cl03'
        e = create_entity(self.manager, entity_type=ENTITY_TYPE, short_code=clinic03)

        e.add_data(data=[("beds", 200), ("meds", 50),
                         ("director", "Dr. C"), ("patients", 12)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        values = data.get_latest(self.manager, entity_type=ENTITY_TYPE)

        self.assertEqual(values[clinic01], {"director": "Dr. A", "beds": 500, "patients": 20, 'meds': 20})
        self.assertEqual(values[clinic02], {"director": "Dr. B2", "beds": 200, "patients": 20, 'meds': 400})
        self.assertEqual(values[clinic03], {"director": "Dr. C", "beds": 200, "patients": 12, 'meds': 50})


    def test_should_filter_aggregate_per_entity_for_a_location(self):
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        FEB = datetime.datetime(2011, 02, 01, tzinfo=UTC)
        MARCH = datetime.datetime(2011, 03, 01, tzinfo=UTC)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        id1_pune = e.save()

        e.add_data(data=[("beds", 300), ("meds", 20),
                         ("director", "Dr. A"), ("patients", 10)],
            event_time=FEB)
        e.add_data(data=[("beds", 500), ("meds", 20),
                         ("patients", 20)],
            event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        id2_pune = e.save()
        e.add_data(data=[("beds", 100), ("meds", 10),
                         ("director", "Dr. AA"), ("patients", 50)],
            event_time=FEB)
        e.add_data(data=[("beds", 200), ("meds", 20),
                         ("patients", 20)],
            event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        id3_pune = e.save()
        e.add_data(data=[("beds", 100), ("meds", 10),
                         ("director", "Dr. AAA"), ("patients", 50)],
            event_time=FEB)
        e.add_data(data=[("beds", 200), ("meds", 20),
                         ("patients", 50)],
            event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        e.save()
        e.add_data(data=[("beds", 100), ("meds", 250),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=FEB)
        e.add_data(data=[("beds", 200), ("meds", 400),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Mumbai'])
        e.save()
        e.add_data(data=[("beds", 200), ("meds", 50),
                         ("director", "Dr. C"), ("patients", 12)],
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
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        FEB = datetime.datetime(2011, 02, 01, tzinfo=UTC)
        MARCH = datetime.datetime(2011, 03, 01, tzinfo=UTC)

        # Entities for State 1: Maharashtra
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        e.save()

        e.add_data(data=[("beds", 300), ("meds", 20),
                         ("director", "Dr. A"), ("patients", 10)],
            event_time=FEB)
        e.add_data(data=[("beds", 500), ("meds", 20),
                         ("patients", 20)],
            event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        e.save()
        e.add_data(data=[("beds", 100), ("meds", 10),
                         ("director", "Dr. AA"), ("patients", 50)],
            event_time=FEB)
        e.add_data(data=[("beds", 200), ("meds", 20),
                         ("patients", 20)],
            event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Mumbai'])
        e.save()
        e.add_data(data=[("beds", 100), ("meds", 10),
                         ("director", "Dr. AAA"), ("patients", 50)],
            event_time=FEB)
        e.add_data(data=[("beds", 200), ("meds", 20),
                         ("patients", 50)],
            event_time=MARCH)

        # Entities for State 2: karnataka
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        e.save()
        e.add_data(data=[("beds", 100), ("meds", 250),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=FEB)
        e.add_data(data=[("beds", 200), ("meds", 400),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=MARCH)
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Hubli'])
        e.save()
        e.add_data(data=[("beds", 100), ("meds", 250),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=FEB)
        e.add_data(data=[("beds", 200), ("meds", 400),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=MARCH)
        # Entities for State 3: Kerala
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Kerala', 'Kochi'])
        e.save()
        e.add_data(data=[("beds", 200), ("meds", 50),
                         ("director", "Dr. C"), ("patients", 12)],
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
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        FEB = datetime.datetime(2011, 02, 01, tzinfo=UTC)
        MARCH = datetime.datetime(2011, 03, 01, tzinfo=UTC)

        # Entities for State 1: Maharashtra
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        e.set_aggregation_path("governance", ["Director", "Med_Officer", "Surgeon"])
        e.save()

        e.add_data(data=[("beds", 300), ("meds", 20),
                         ("director", "Dr. A"), ("patients", 10)],
            event_time=FEB)
        e.add_data(data=[("beds", 500), ("meds", 20),
                         ("patients", 20)],
            event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        e.set_aggregation_path("governance", ["Director", "Med_Supervisor", "Surgeon"])
        e.save()

        e.add_data(data=[("beds", 100), ("meds", 10),
                         ("director", "Dr. AA"), ("patients", 50)],
            event_time=FEB)
        e.add_data(data=[("beds", 200), ("meds", 20),
                         ("patients", 20)],
            event_time=MARCH)

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Mumbai'])
        e.set_aggregation_path("governance", ["Director", "Med_Officer", "Doctor"])
        e.save()

        e.add_data(data=[("beds", 100), ("meds", 10),
                         ("director", "Dr. AAA"), ("patients", 50)],
            event_time=FEB)
        e.add_data(data=[("beds", 200), ("meds", 20),
                         ("patients", 50)],
            event_time=MARCH)

        # Entities for State 2: karnataka
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        e.set_aggregation_path("governance", ["Director", "Med_Supervisor", "Nurse"])
        e.save()
        e.add_data(data=[("beds", 100), ("meds", 250),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=FEB)
        e.add_data(data=[("beds", 200), ("meds", 400),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=MARCH)
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Hubli'])
        e.set_aggregation_path("governance", ["Director", "Med_Officer", "Surgeon"])
        e.save()
        e.add_data(data=[("beds", 100), ("meds", 250),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=FEB)
        e.add_data(data=[("beds", 200), ("meds", 400),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=MARCH)

        # Entities for State 3: Kerala
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Kerala', 'Kochi'])
        e.set_aggregation_path("governance", ["Director", "Med_Officer", "Nurse"])
        e.save()
        e.add_data(data=[("beds", 200), ("meds", 50),
                         ("director", "Dr. C"), ("patients", 12)],
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


    def test_should_fetch_aggregate_per_entity_for_all_fields_in_entity(self):
        # Aggregate across all data records for each entity for all fields

        # Setup: Create clinic entities
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Pune'])
        id1 = e.save()
        e.add_data(data=[("beds", 300), ("meds", 20),
                         ("director", "Dr. A"), ("patients", 10)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 500), ("meds", 20),
                         ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'Karnataka', 'Bangalore'])
        id2 = e.save()
        e.add_data(data=[("beds", 100), ("meds", 250),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC))
        e.add_data(data=[("beds", 200), ("meds", 400),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=['India', 'MH', 'Mumbai'])
        id3 = e.save()
        e.add_data(data=[("beds", 200), ("meds", 50),
                         ("director", "Dr. C"), ("patients", 12)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC))

        #        values = data.fetch(self.manager, entity_type=ENTITY_TYPE, aggregates={"*": data.reduce_functions.LATEST})
        values = data.aggregate(self.manager, entity_type=ENTITY_TYPE,
            aggregates={"*": data.reduce_functions.LATEST},
            aggregate_on=EntityAggregration())

        self.assertEqual(len(values), 3)
        self.assertEqual(values[id1], {"director": "Dr. A", "beds": 500, "patients": 20, "meds": 20})
        self.assertEqual(values[id2], {"director": "Dr. B2", "beds": 200, "patients": 20, "meds": 400})
        self.assertEqual(values[id3], {"director": "Dr. C", "beds": 200, "patients": 12, "meds": 50})

#remove_datadict_type
    #def test_get_entities_by_value(self):
    #
    #    jan = datetime.datetime(2011, 01, 01, tzinfo=UTC)
    #    feb = datetime.datetime(2011, 02, 01, tzinfo=UTC)
    #    march = datetime.datetime(2011, 03, 01, tzinfo=UTC)
    #    april = datetime.datetime(2011, 04, 01, tzinfo=UTC)
    #    may = datetime.datetime(2011, 05, 03, tzinfo=UTC)
    #
    #    e = Entity(self.manager, entity_type='foo')
    #    e.save()
    #    data_record = [('meds', 20),
    #                   ('doc', "aroj"),
    #                   ('facility', 'clinic')]
    #    e.add_data(data_record, event_time=feb)
    #
    #    f = Entity(self.manager, entity_type='bar')
    #    f.save()
    #    data_record = [('meds', 10),
    #                   ('doc', "aroj"),
    #                   ('facility', 'clinic')]
    #    f.add_data(data_record, event_time=jan)
    #    data_record = [('foo', 20),
    #                   ('doc', "aroj"),
    #                   ('facility', 'clinic')]
    #    f.add_data(data_record, event_time=march)
    #    data_record = [('bar', 30),
    #                   ('doc', "aroj"),
    #                   ('facility', 'clinic')]
    #    f.add_data(data_record, event_time=april)
    #
    #    # datadict_type, no as_of
    #    entity_ids = [x.id for x in get_entities_by_value(self.manager, 20)]
    #    self.assertTrue(e.id in entity_ids)
    #    self.assertTrue(f.id not in entity_ids)
    #    # label, no as_of
    #    entity_ids = [x.id for x in get_entities_by_value(self.manager, 'foo', 20)]
    #    self.assertTrue(e.id not in entity_ids)
    #    self.assertTrue(f.id in entity_ids)
    #    # datadict_type, with as_of
    #    entity_ids = [x.id for x in get_entities_by_value(self.manager, 10, as_of=feb)]
    #    self.assertTrue(e.id not in entity_ids)
    #    self.assertTrue(f.id in entity_ids)
    #    # label, with as_of
    #    entity_ids = [x.id for x in get_entities_by_value(self.manager, 'bar', 30, as_of=may)]
    #    self.assertTrue(e.id not in entity_ids)
    #    self.assertTrue(f.id in entity_ids)
    #    # TODO: more tests for different types?

    def test_check_entity_exists_with_value(self):
        e = Entity(self.manager, entity_type='foo')
        e.save()
        data_record = [('meds', 20),
                       ('doc', "aroj"),
                       ('facility', 'clinic')]
        e.add_data(data_record, event_time=(datetime.datetime(2011, 02, 01, tzinfo=UTC)))

        self.assertTrue(entities_exists_with_value(self.manager, ['foo'], 'meds', 20))
        self.assertTrue(entities_exists_with_value(self.manager, ['foo'], 'doc', 'aroj'))

        self.assertFalse(entities_exists_with_value(self.manager, ['foo'], 'meds', 21))
        self.assertFalse(entities_exists_with_value(self.manager, ['foo'], 'doc', "akshay"))
        self.assertFalse(entities_exists_with_value(self.manager, ['bar'], 'meds', 20))
        self.assertFalse(entities_exists_with_value(self.manager, ['foo'], 'test_field', 20))


    def test_should_aggregate_per_entity_per_form_model(self):
        ENTITY_TYPE = ["HealthFacility", "Clinic"]
        self.create_clinic_type(ENTITY_TYPE)
        self._create_form_model("CL2")
        self._create_form_model("CL1")
        e, id1 = self.create_entity_instance(ENTITY_TYPE, ['India', 'MH', 'Pune'])

        e.add_data(data=[("beds", 300), ("meds", 20),
                         ("director", "Dr. A"), ("patients", 10)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='CL1'))
        e.add_data(data=[("beds", 500), ("meds", 50),
                         ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
            submission=dict(submission_id='2', form_code='CL1'))

        e.add_data(data=[("beds", 300), ("doctors", 20),
                         ("director", "Dr. A"), ("patients", 10)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='CL2'))

        e.add_data(data=[("beds", 200), ("doctors", 10),
                         ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
            submission=dict(submission_id='2', form_code='CL2'))

        e, id2 = self.create_entity_instance(ENTITY_TYPE, ['India', 'Karnataka', 'Bangalore'])

        e.add_data(data=[("beds", 100), ("meds", 250),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='3', form_code='CL1'))
        e.add_data(data=[("beds", 200), ("meds", 400),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
            submission=dict(submission_id='4', form_code='CL1'))

        e.add_data(data=[("beds", 150), ("doctors", 50),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='3', form_code='CL2'))
        e.add_data(data=[("beds", 270), ("doctors", 40),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
            submission=dict(submission_id='4', form_code='CL2'))

        e, id3 = self.create_entity_instance(ENTITY_TYPE, ['India', 'MH', 'Mumbai'])
        e.add_data(data=[("beds", 200), ("meds", 50),
                         ("director", "Dr. C"), ("patients", 12)],
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

    def _add_data_for_form_1(self, e):
        e.add_data(data=[("beds", 300), ("meds", 20),
                         ("director", "Dr. A"), ("patients", 10)],
            event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='CL1'))
        e.add_data(data=[("beds", 500), ("meds", 50),
                         ("patients", 20)],
            event_time=datetime.datetime(2010, 03, 01, tzinfo=UTC),
            submission=dict(submission_id='2', form_code='CL1'))
        e.add_data(data=[("beds", 300), ("doctors", 20),
                         ("director", "Dr. A1"), ("patients", 10)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='CL1'))
        e.add_data(data=[("beds", 200), ("meds", 10),
                         ("patients", 20), ("director", "Dr. A2")],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
            submission=dict(submission_id='2', form_code='CL1'))

    def _add_data_for_form_2(self, e):
        e.add_data(data=[("beds", 200), ("meds", 20),
                         ("patients", 45)],
            event_time=datetime.datetime(2011, 04, 01, tzinfo=UTC),
            submission=dict(submission_id='2', form_code='CL2'))

    def _add_data_for_form_1_entity_2(self, e):
        e.add_data(data=[("beds", 100), ("meds", 250),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='3', form_code='CL1'))
        e.add_data(data=[("beds", 200), ("meds", 400),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=datetime.datetime(2010, 03, 01, tzinfo=UTC),
            submission=dict(submission_id='4', form_code='CL1'))
        e.add_data(data=[("beds", 150), ("meds", 50),
                         ("director", "Dr. B1"), ("patients", 50)],
            event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='3', form_code='CL1'))

    def _add_data_form_2_entity_2(self, e):
        e.add_data(data=[("beds", 270), ("doctors", 40),
                         ("director", "Dr. B2"), ("patients", 20)],
            event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
            submission=dict(submission_id='4', form_code='CL2'))

    def test_should_aggregate_per_entity_per_form_model_with_time_filter(self):
        test_data = TestData(self.manager)

        values = aggregate_by_form_code_python(dbm=self.manager, form_code='CL1',
            aggregate_on=EntityAggregration(),
            aggregates=[Sum("patients"), Min('meds'), Max('beds'),
                        Latest("director")],
            starttime="01-01-2011 00:00:00", endtime="31-12-2011 00:00:00")

        self.assertEqual(len(values), 2)
        self.assertEqual(values[test_data.entity1.id], {"patients": 30, 'meds': 10, 'beds': 300, 'director': "Dr. A2"})
        self.assertEqual(values[test_data.entity2.id], {"patients": 50, 'meds': 50, 'beds': 150, 'director': "Dr. B1"})


    def test_aggregation_factory(self):
        test_object = aggregation_factory("sum", "patients")
        self.assertEquals(6, test_object.reduce([1, 2, 3]))
        self.assertEquals("patients", test_object.field_name)

    def create_entity_instance(self, ENTITY_TYPE, location):
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=location)
        id1 = e.save()
        return e, id1

    def create_clinic_type(self, entity_type):
        self.entity_type = entity_type
        define_type(self.manager, entity_type)


    def _create_form_model(self, form_code):
        question1 = UniqueIdField(unique_id_type=self.entity_type[0],name="entity_question1", code="ID1", label="What is associated clinic entity")
        question5 = UniqueIdField(unique_id_type=self.entity_type[1],name="entity_question2", code="ID2", label="What is associated health facility entity")
        question2 = TextField(name="question1_Name", code="Q1", label="What is your name",
            defaultValue="some default value")
        question3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age")
        question4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
            options=[("RED", 1), ("YELLOW", 2)])

        self.form_model = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
            form_code=form_code, type='survey', fields=[
                question1, question2, question3, question4])
        self.form_model__id = self.form_model.save()


    def test_should_return_grand_total_for_all_records(self):
        ENTITY_TYPE = ["HealthFacility", "Clinic"]
        self.create_clinic_type(ENTITY_TYPE)
        self._create_form_model("CL2")
        self._create_form_model("CL1")
        e, id1 = self.create_entity_instance(ENTITY_TYPE, ['India', 'MH', 'Pune'])

        self._add_data_for_form_1(e)

        self._add_data_for_form_2(e)

        e, id2 = self.create_entity_instance(ENTITY_TYPE, ['India', 'Karnataka', 'Bangalore'])

        self._add_data_for_form_1_entity_2(e)
        self._add_data_form_2_entity_2(e)

        values = aggregate_by_form_code_python(dbm=self.manager, form_code='CL1',
            aggregate_on=None,
            aggregates=[Sum("patients"), Sum('meds'), Sum('beds')],
        )

        self.assertEqual(
            dict(GrandTotals={'patients': 180, 'meds': 780, 'beds': 1750, 'director': None, 'doctors': 20}), values)


    def test_should_return_grand_total_and_aggregate_per_entity(self):
        test_data = TestData(self.manager)

        values = aggregate_by_form_code_python(dbm=self.manager, form_code='CL1',
            aggregate_on=EntityAggregration(),
            aggregates=[Sum("patients"), Min('meds'), Max('beds'),
                        Latest("director")],
            include_grand_totals=True
        )

        print values
        self.assertEqual(len(values), 4)
        self.assertDictEqual({"patients": 60, 'meds': 10, 'beds': 500, 'director': "Dr. A2"},
            values[test_data.entity1.id])
        self.assertEqual({"patients": 120, 'meds': 50, 'beds': 200, 'director': "Dr. B1"}, values[test_data.entity2.id])
        self.assertEqual({"patients": 12, 'meds': 50, 'beds': 200, 'director': "Dr. C"}, values[test_data.entity3.id])
        self.assertEqual({'patients': 192, 'meds': 830, 'beds': 1950, 'director': None, 'doctors': 20, 'name':None},
            values["GrandTotals"])






