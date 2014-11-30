import datetime
from mangrove.bootstrap import initializer
from mangrove.datastore.documents import SurveyResponseDocument
from mangrove.datastore.entity import create_entity
from mangrove.transport.repository.reporters import get_reporters_who_submitted_data_for_frequency_period
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase


class TestShouldSaveSMSSurveyResponse(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)
        initializer.run(self.manager)

    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def test_get_reporters_who_submitted_data_for_frequency_period(self):
        self.ds1 = create_entity(self.manager, entity_type=["reporter"],
                                 location=["India", "Pune"], aggregation_paths=None, short_code="ds_reminder_int_1")
        self.ds1.add_data(data=[("entity_type", "reporter")])

        self.manager._save_document(SurveyResponseDocument(channel="transport",
                                                           destination=12345, form_model_id="abc",
                                                           values={'Q1': 'ans1', 'Q2': 'ans2'},
                                                           status=False, error_message="", data_record_id='2345678',
                                                           owner_uid=self.ds1.id,
                                                           event_time=datetime.datetime(2011, 9, 1)))
        self.manager._save_document(SurveyResponseDocument(channel="transport",
                                                           destination=12345, form_model_id="abc",
                                                           values={'Q1': 'ans12', 'Q2': 'ans22'},
                                                           owner_uid=self.ds1.id,
                                                           status=False, error_message="", data_record_id='1234567',
                                                           event_time=datetime.datetime(2011, 3, 3)))

        from_time = datetime.datetime(2011, 3, 1)
        end_time = datetime.datetime(2011, 3, 30)

        reporters = get_reporters_who_submitted_data_for_frequency_period(self.manager, "abc", from_time, end_time)
        self.assertEquals(1, len(reporters))