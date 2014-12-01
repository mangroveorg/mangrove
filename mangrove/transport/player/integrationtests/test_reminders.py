import random
import datetime
from mangrove.bootstrap import initializer
from mangrove.datastore.documents import SurveyResponseDocument
from mangrove.datastore.entity import create_entity
from mangrove.form_model.project import Project
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase


class TestShouldSaveSMSSurveyResponse(MangroveTestCase):
    def create_datasender(self):
        ds = create_entity(self.manager, entity_type=["reporter"],
                           location=["India", "Pune"], aggregation_paths=None,
                           short_code=''.join(random.sample('abcdefghijklmnopqrs', 6)))
        ds.add_data(data=[("entity_type", "reporter")])
        return ds

    def setUp(self):
        MangroveTestCase.setUp(self)
        initializer.run(self.manager)
        self.ds1 = self.create_datasender()
        self.ds2 = self.create_datasender()
        self.project = Project(self.manager, name="Test reminders",
                               form_code="abc",
                               fields=[], goals="This project is for automation",
                               devices=["sms", "web", "smartPhone"], sender_group="close"
        )
        self.manager._save_document(SurveyResponseDocument(channel="transport",
                                                           destination=12345, form_model_id=self.project.id,
                                                           values={'Q1': 'ans1', 'Q2': 'ans2'},
                                                           status=False, error_message="", data_record_id='2345678',
                                                           owner_uid=self.ds1.id,
                                                           event_time=datetime.datetime(2011, 9, 1)))
        self.manager._save_document(SurveyResponseDocument(channel="transport",
                                                           destination=12345, form_model_id=self.project.id,
                                                           values={'Q1': 'ans12', 'Q2': 'ans22'},
                                                           owner_uid=self.ds1.id,
                                                           status=False, error_message="", data_record_id='1234567',
                                                           event_time=datetime.datetime(2011, 3, 2)))
        self.manager._save_document(SurveyResponseDocument(channel="transport",
                                                           destination=12345, form_model_id=self.project.id,
                                                           values={'Q1': 'ans123', 'Q2': 'ans222'},
                                                           owner_uid=self.ds2.id,
                                                           status=False, error_message="", data_record_id='1234567',
                                                           event_time=datetime.datetime(2011, 3, 3)))


    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def test_get_data_senders_ids_who_made_submission_in_week(self):
        deadline = datetime.date(2011, 3, 4)
        reporters = self.project._get_data_senders_ids_who_made_submission_for(self.manager, deadline, 'week')
        self.assertEquals(2, len(reporters))