from mangrove.datastore.data import EntityAggregration
from mangrove.datastore.tests.test_data import TestData
from mangrove.datastore.time_period_aggregation import aggregate_for_time_period, Sum, Min, Max, Month, Latest, Week, Year
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestTimeGroupedAggregation(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)
        self.test_data = TestData(self.manager)

    def test_monthly_time_aggregation(self):
        values = aggregate_for_time_period(dbm=self.manager, form_code='CL1',
                                           aggregate_on=EntityAggregration(),
                                           aggregates=[Sum("patients"), Min('meds'), Max('beds'),
                                                       ],
                                           period=Month(2, 2010))

        self.assertEqual(len(values), 2)
        self.assertEqual(values[self.test_data.entity1.short_code], {"patients": 10, 'meds': 20, 'beds': 300 })
        self.assertEqual(values[self.test_data.entity2.short_code], {"patients": 50, 'meds': 250, 'beds': 100})


    def test_monthly_time_aggregation_with_latest(self):
        values = aggregate_for_time_period(dbm=self.manager, form_code='CL1',
                                           aggregate_on=EntityAggregration(),
                                           aggregates=[Sum("patients"), Latest("director"),
                                                       ],
                                           period=Month(2, 2010))

        self.assertEqual(len(values), 2)
        self.assertEqual(values[self.test_data.entity1.short_code], {"patients": 10, 'director': "Dr. A"})
        self.assertEqual(values[self.test_data.entity2.short_code], {"patients": 50, 'director': "Dr. B1"})

    def test_weekly_time_aggregation(self):
        self.test_data.add_weekly_data_for_entity1()
        values = aggregate_for_time_period(dbm=self.manager, form_code='CL1',
                                           aggregate_on=EntityAggregration(),
                                           aggregates=[Min("patients"), Sum("beds")
                                                       ],
                                           period=Week(52, 2009))

        self.assertEqual(len(values), 1)
        self.assertEqual(values[self.test_data.entity1.short_code], {"patients": 20, 'beds':450})

    def test_weekly_time_aggregation_with_latest(self):
        self.test_data.add_weekly_data_for_entity1()
        values = aggregate_for_time_period(dbm=self.manager, form_code='CL1',
                                           aggregate_on=EntityAggregration(),
                                           aggregates=[Min("patients"), Latest("director")
                                                       ],
                                           period=Week(52, 2009))

        self.assertEqual(len(values), 1)
        self.assertEqual(values[self.test_data.entity1.short_code], {"patients": 20, 'director':'Dr. B2'})

    def test_yearly_time_aggregation_with_latest(self):
        values = aggregate_for_time_period(dbm=self.manager, form_code='CL1',
                                           aggregate_on=EntityAggregration(),
                                           aggregates=[Min("patients"), Latest("director"),Sum("beds")
                                                       ],
                                           period=Year(2010))

        self.assertEqual(len(values), 3)
        self.assertEqual(values[self.test_data.entity1.short_code], {"patients": 10, "beds": 800,'director':'Dr. A'})
        self.assertEqual(values[self.test_data.entity2.short_code], {"patients": 20, "beds": 300,'director':'Dr. B2'})
        self.assertEqual(values[self.test_data.entity3.short_code], {"patients": 12, "beds": 200,'director':'Dr. C'})




