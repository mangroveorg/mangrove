# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import datetime
from pytz import UTC
from mangrove.datastore.documents import DataRecordDocument
from mangrove.datastore.entity import get_data_record
from mangrove.datastore.tests.test_data import TestData
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestDataRecords(MangroveTestCase):
    def test_add_data_record_to_entity(self):
        test_data = TestData(self.manager)
        data_record = [('meds', 20, test_data.dd_types['meds']),
            ('doc', "aroj", test_data.dd_types['doctors']),
            ('facility', 'clinic', test_data.dd_types['facility']),
            ('opened_on', datetime(2011, 01, 02, tzinfo=UTC), test_data.dd_types['facility'])]
        data_record_id = test_data.entity1.add_data(data=data_record,
                                                    event_time=datetime(2011, 01, 02, tzinfo=UTC),
                                                    submission=dict(submission_id="123456"))
        self.assertTrue(data_record_id is not None)

        # Assert the saved document structure is as expected
        saved = get_data_record(self.manager,data_record_id)
        for (label, value, dd_type) in data_record:
            self.assertTrue(label in saved.data)
            self.assertTrue('value' in saved.data[label])
            self.assertTrue('type' in saved.data[label])
            self.assertTrue(value == saved.data[label]['value'])
            # TODO: not sure how to test that dd_type == saved.data[label]['type']
            # it seems the following has different representations for datetimes
            #self.assertTrue(dd_type._doc.unwrap() == DataDictDocument(saved.data[label]['type']))
        self.assertEqual(saved.event_time, datetime(2011, 01, 02, tzinfo=UTC))
        self.assertEqual(saved.submission['submission_id'], "123456")

