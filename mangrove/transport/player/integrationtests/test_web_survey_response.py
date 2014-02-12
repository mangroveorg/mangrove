
#  This is an integration test.
# Send message via web, parse them and save.

from time import mktime
import datetime
from mangrove.transport.player.new_players import WebPlayerV2
from mangrove.bootstrap import initializer
from mangrove.datastore.documents import SurveyResponseDocument
from mangrove.datastore.entity import create_entity
from mangrove.datastore.entity_type import define_type

from mangrove.form_model.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import FormModel, NAME_FIELD, MOBILE_NUMBER_FIELD
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint
from mangrove.transport.contract.transport_info import TransportInfo
from mangrove.transport.contract.request import Request
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.transport.repository.survey_responses import get_survey_responses, get_survey_responses_for_activity_period


class TestWEBSurveyResponse(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)
        initializer.run(self.manager)
        define_type(self.manager, ["dog"])
        self.entity_type = ["clinic"]
        define_type(self.manager, self.entity_type)

        self.entity = create_entity(self.manager, entity_type=self.entity_type,
                                    location=["India", "Pune"], aggregation_paths=None, short_code="cli1",
        )
        self.data_record_id = self.entity.add_data(data=[("Name", "Ruby")],
                                                   submission=dict(submission_id="1"))

        self.reporter = create_entity(self.manager, entity_type=["reporter"],
                                      location=["India", "Pune"], aggregation_paths=None, short_code="rep1",
        )
        self.reporter.add_data(data=[(MOBILE_NUMBER_FIELD, '1234'),
                                     (NAME_FIELD, "Test_reporter")], submission=dict(submission_id="2"))

        #Web submission Form Model
        question1 = TextField(name="entity_question", code="EID", label="What is associated entity",
                              entity_question_flag=True)
        question2 = TextField(name="Name", code="NAME", label="Clinic Name",
                              defaultValue="some default value",
                              constraints=[TextLengthConstraint(4, 15)], required=False)
        question3 = IntegerField(name="Arv stock", code="ARV", label="ARV Stock",
                                 constraints=[NumericRangeConstraint(min=15, max=120)],
                                 required=False)
        question4 = SelectField(name="Color", code="COL", label="Color",
                                options=[("RED", 1), ("YELLOW", 2)], required=False)
        self.form_model = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                    form_code="clinic", type='survey',
                                    fields=[question1, question2, question3, question4])
        self.form_model.save()

        #Activity Report Form Model
        question1 = TextField(name="entity_question", code="EID", label="What is associated entity",
                              entity_question_flag=True)
        question2 = TextField(name="Name", code="NAME", label="Clinic Name",
                              defaultValue="some default value",
                              constraints=[TextLengthConstraint(4, 15)])
        question3 = IntegerField(name="Arv stock", code="ARV", label="ARV Stock",
                                 constraints=[NumericRangeConstraint(min=15, max=120)])
        activity_report = FormModel(self.manager, entity_type=["reporter"], name="report", label="reporting form_model",
                                    form_code="acp", type='survey', fields=[question1, question2, question3])
        activity_report.save()

        self.web_player = WebPlayerV2(self.manager)

    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def add_survey_response(self, text, reporter_id='rep12'):
        transport_info = TransportInfo(transport="web", source="tester150411@gmail.com", destination="")
        response = self.web_player.add_survey_response(Request(message=text, transportInfo=transport_info), reporter_id)
        return response


    def test_should_get_survey_responses_for_form(self):
        self.manager._save_document(
            SurveyResponseDocument(channel="web", destination="", form_code="abc",
                                   values={'Q1': 'ans1', 'Q2': 'ans2'},
                                   status=False, error_message="", data_record_id='2345678'))
        self.manager._save_document(
            SurveyResponseDocument(channel="web", destination="", form_code="abc",
                                   values={'Q1': 'ans12', 'Q2': 'ans22'},
                                   status=False, error_message="", data_record_id='1234567'))
        self.manager._save_document(
            SurveyResponseDocument(channel="web", destination="", form_code="def",
                                   values={'defQ1': 'defans12', 'defQ2': 'defans22'},
                                   status=False, error_message="", data_record_id='345678'))

        oneDay = datetime.timedelta(days=1)
        tomorrow = datetime.datetime.now() + oneDay
        survey_responses = get_survey_responses(self.manager, "abc", 0, int(mktime(tomorrow.timetuple())) * 1000)
        self.assertEquals(2, len(survey_responses))
        self.assertEquals({'Q1': 'ans12', 'Q2': 'ans22'}, survey_responses[0].values)
        self.assertEquals({'Q1': 'ans1', 'Q2': 'ans2'}, survey_responses[1].values)

    def test_error_messages_are_being_logged_in_survey_responses(self):
        text = {'form_code': 'clinic', 'EID': self.entity.short_code, 'ARV': '150'}
        self.add_survey_response(text,reporter_id="rep1")
        oneDay = datetime.timedelta(days=1)
        tomorrow = datetime.datetime.now() + oneDay
        survey_responses = get_survey_responses(self.manager, "clinic", 0, int(mktime(tomorrow.timetuple())) * 1000)
        self.assertEquals(1, len(survey_responses))
        self.assertEquals(u"Answer 150 for question ARV is greater than allowed.", survey_responses[0].errors)

    def test_get_submissions_for_form_for_an_activity_period(self):
        self.manager._save_document(
            SurveyResponseDocument(channel="web", destination="", form_code="abc",
                                   values={'Q1': 'ans1', 'Q2': 'ans2'},
                                   status=False, error_message="", data_record_id='2345678',
                                   event_time=datetime.datetime(2011, 9, 1)))
        self.manager._save_document(
            SurveyResponseDocument(channel="web", destination="", form_code="abc",
                                   values={'Q1': 'ans12', 'Q2': 'ans22'},
                                   status=False, error_message="", data_record_id='1234567',
                                   event_time=datetime.datetime(2011, 3, 3)))
        self.manager._save_document(
            SurveyResponseDocument(channel="web", destination="", form_code="abc",
                                   values={'Q1': 'ans12', 'Q2': 'defans22'},
                                   status=False, error_message="", data_record_id='345678',
                                   event_time=datetime.datetime(2011, 3, 10)))

        from_time = datetime.datetime(2011, 3, 1)
        end_time = datetime.datetime(2011, 3, 30)

        survey_responses = get_survey_responses_for_activity_period(self.manager, "abc", from_time, end_time)
        self.assertEquals(2, len(survey_responses))


class LocationTree(object):
    def get_location_hierarchy_for_geocode(self, lat, long):
        return ['madagascar']

    def get_centroid(self, location_name, level):
        return 60, -12

    def get_location_hierarchy(self, lowest_level_location_name):
        return [u'arantany']
