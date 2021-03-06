

#  This is an integration test.
# Send sms, parse and save.
from time import mktime
import datetime
from mangrove.bootstrap import initializer
from mangrove.datastore.documents import   SurveyResponseDocument
from mangrove.datastore.entity import  create_entity
from mangrove.datastore.entity_type import define_type
from mangrove.form_model.field import TextField, IntegerField, SelectField, UniqueIdField
from mangrove.form_model.form_model import FormModel, NAME_FIELD, MOBILE_NUMBER_FIELD
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint
from mangrove.transport.contract.transport_info import TransportInfo
from mangrove.transport.contract.request import Request
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.transport.player.new_players import SMSPlayerV2
from mangrove.transport.player.player import SMSPlayer
from mangrove.transport.repository.survey_responses import survey_response_count, get_survey_responses, get_survey_responses_for_activity_period

class LocationTree(object):
    def get_location_hierarchy_for_geocode(self, lat, long ):
        return ['madagascar']

    def get_centroid(self, location_name, level):
        return 60, -12

    def get_location_hierarchy(self, lowest_level_location_name):
        return [u'arantany']

FORM_MODEL_ID = "abc"

class TestShouldSaveSMSSurveyResponse(MangroveTestCase):

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

        question1 = UniqueIdField('clinic',name="entity_question", code="EID", label="What is associated entity")
        question2 = TextField(name="Name", code="NAME", label="Clinic Name",
            defaultValue="some default value",
            constraints=[TextLengthConstraint(4, 15)] , required=False)
        question3 = IntegerField(name="Arv stock", code="ARV", label="ARV Stock",
            constraints=[NumericRangeConstraint(min=15, max=120)] , required=False)
        question4 = SelectField(name="Color", code="COL", label="Color",
            options=[("RED", 1), ("YELLOW", 2)] , required=False)

        self.form_model = FormModel(self.manager,  name="aids", label="Aids form_model",
            form_code="clinic", fields=[question1, question2, question3])
        self.form_model.add_field(question4)
        self.form_model_id = self.form_model.save()

        self.submission_handler = None
        self.sms_player = SMSPlayer(self.manager, LocationTree())
        self.sms_player_v2 = SMSPlayerV2(self.manager, [])

    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def _prepare_survey_responses(self):
        doc_id1 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", destination=12345, form_model_id=FORM_MODEL_ID,
                values={'Q1': 'ans1', 'Q2': 'ans2'}, status=True, error_message=""))
        doc_id2 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", destination=12345, form_model_id=FORM_MODEL_ID,
                values={'Q1': 'ans12', 'Q2': 'ans22'}, status=True, error_message=""))
        doc_id3 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", destination=12345, form_model_id=FORM_MODEL_ID,
                values={'Q3': 'ans12', 'Q4': 'ans22'}, status=False, error_message=""))
        doc_id4 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", destination=12345, form_model_id="def",
                values={'defQ1': 'defans12', 'defQ2': 'defans22'}, status=False, error_message=""))
        return [doc_id1, doc_id2, doc_id3, doc_id4]


    def test_count_of_survey_responses_should_be_zero_when_form_code_not_existed(self):
        self._prepare_survey_responses()
        count = survey_response_count(self.manager, "not_existed_form_code", 0, self._tomorrow())
        self.assertEqual(0, count)

    def test_get_survey_responses_for_form(self):
        self._prepare_survey_responses()
        survey_responses = get_survey_responses(self.manager, FORM_MODEL_ID, 0, self._tomorrow())
        self.assertEquals(3, len(survey_responses))
        self.assertEquals({'Q3': 'ans12', 'Q4': 'ans22'}, survey_responses[0].values)
        self.assertEquals({'Q1': 'ans12', 'Q2': 'ans22'}, survey_responses[1].values)
        self.assertEquals({'Q1': 'ans1', 'Q2': 'ans2'}, survey_responses[2].values)


    def test_error_messages_are_being_logged_in_survey_responses(self):
        text = "clinic .EID %s .ARV 150 " % self.entity.short_code
        self.send_sms_v2(text)
        survey_responses = get_survey_responses(self.manager, self.form_model_id, 0, self._tomorrow())
        self.assertEquals(1, len(survey_responses))
        self.assertEquals(u"Answer 150 for question ARV is greater than allowed.", survey_responses[0].errors)

    def test_get_survey_responses_for_form_for_an_activity_period(self):
        self.manager._save_document(SurveyResponseDocument(channel="transport",
            destination=12345, form_model_id="abc",
            values={'Q1': 'ans1', 'Q2': 'ans2'},
            status=False, error_message="", data_record_id='2345678', event_time=datetime.datetime(2011, 9, 1)))
        self.manager._save_document(SurveyResponseDocument(channel="transport",
            destination=12345, form_model_id="abc",
            values={'Q1': 'ans12', 'Q2': 'ans22'},
            status=False, error_message="", data_record_id='1234567', event_time=datetime.datetime(2011, 3, 3)))
        self.manager._save_document(SurveyResponseDocument(channel="transport",
            destination=12345, form_model_id="abc",
            values={'Q1': 'ans12', 'Q2': 'defans22'},
            status=False, error_message="", data_record_id='345678', event_time=datetime.datetime(2011, 3, 10)))

        from_time = datetime.datetime(2011, 3, 1)
        end_time = datetime.datetime(2011, 3, 30)

        submissions = get_survey_responses_for_activity_period(self.manager, "abc", from_time, end_time)
        self.assertEquals(2, len(submissions))

    def send_sms(self, text):
        transport_info = TransportInfo(transport="sms", source="1234", destination="5678")
        response = self.sms_player.accept(Request(message=text, transportInfo=transport_info))
        return response

    def send_sms_v2(self, text):
        transport_info = TransportInfo(transport="sms", source="1234", destination="5678")
        response = self.sms_player_v2.add_survey_response(Request(message=text, transportInfo=transport_info))
        return response

    def _tomorrow(self):
        oneDay = datetime.timedelta(days=1)
        tomorrow = datetime.datetime.now() + oneDay
        return int(mktime(tomorrow.timetuple())) * 1000
