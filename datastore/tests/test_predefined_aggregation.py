from mangrove.datastore.data import EntityAggregration
from mangrove.datastore.tests.test_data import TestData
from mangrove.datastore.time_period_aggregation import aggregate_for_time_period, Sum, Min, Max, Month
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
        self.assertEqual(values[self.test_data.entity1.short_code], {"patients": 10, 'meds': 20, 'beds': 300, })
        self.assertEqual(values[self.test_data.entity2.short_code], {"patients": 50, 'meds': 250, 'beds': 100})

