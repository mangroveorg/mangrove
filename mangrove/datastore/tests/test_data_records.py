
from datetime import datetime
from pytz import UTC
from mangrove.datastore.entity import  DataRecord
from mangrove.datastore.tests.test_data import TestData
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestDataRecords(MangroveTestCase):
    def test_add_data_record_to_entity(self):
        test_data = TestData(self.manager)
        data_record = [('meds', 20),
            ('doc', "aroj"),
            ('facility', 'clinic'),
            ('opened_on', datetime(2011, 01, 02, tzinfo=UTC))]
        data_record_id = test_data.entity1.add_data(data=data_record,
                                                    event_time=datetime(2011, 01, 02, tzinfo=UTC),
                                                    submission=dict(submission_id="123456"))
        self.assertTrue(data_record_id is not None)

        # Assert the saved document structure is as expected
        saved = DataRecord.get(self.manager, data_record_id)
        for (label, value) in data_record:
            self.assertTrue(label in saved.data)
            self.assertTrue('value' in saved.data[label])
            self.assertTrue(value == saved.data[label]['value'])
        self.assertEqual(saved.event_time, datetime(2011, 01, 02, tzinfo=UTC))
        self.assertEqual(saved.submission['submission_id'], "123456")

