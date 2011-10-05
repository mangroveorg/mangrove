# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

#  This is an integration test.
# Send sms, parse and save.
from time import mktime
import unittest
import datetime
from nose.plugins.skip import SkipTest
from  mangrove import initializer
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.documents import SubmissionLogDocument, DataRecordDocument
from mangrove.datastore.entity import get_by_short_code, create_entity
from mangrove.datastore.entity_type import define_type
from mangrove.errors.MangroveException import  DataObjectAlreadyExists, EntityTypeDoesNotExistsException, InactiveFormModelException, GeoCodeFormatException, MultipleReportersForANumberException, MobileNumberMissing

from mangrove.form_model.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import FormModel, NAME_FIELD, MOBILE_NUMBER_FIELD
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint
from mangrove.transport.player.player import SMSPlayer, Request, TransportInfo
from mangrove.datastore.datadict import DataDictType
from mangrove.transport.submissions import get_submissions, get_submissions_for_activity_period


class LocationTree(object):
    def get_hierarchy_path(self, location_name):
        return location_name

    def get_location_hierarchy_for_geocode(self, lat, long ):
        return ['madagascar']

    def get_centroid(self, location_name, level):
        return 60, -12


class TestShouldSaveSMSSubmission(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        initializer.run(self.dbm)
        define_type(self.dbm, ["dog"])
        self.entity_type = ["healthfacility", "clinic"]
        define_type(self.dbm, self.entity_type)
        self.name_type = DataDictType(self.dbm, name='Name', slug='name', primitive_type='string')
        self.telephone_number_type = DataDictType(self.dbm, name='telephone_number', slug='telephone_number',
                                                  primitive_type='string')
        self.entity_id_type = DataDictType(self.dbm, name='Entity Id Type', slug='entity_id', primitive_type='string')
        self.stock_type = DataDictType(self.dbm, name='Stock Type', slug='stock', primitive_type='integer')
        self.color_type = DataDictType(self.dbm, name='Color Type', slug='color', primitive_type='string')

        self.name_type.save()
        self.telephone_number_type.save()
        self.stock_type.save()
        self.color_type.save()

        self.entity = create_entity(self.dbm, entity_type=self.entity_type,
                                    location=["India", "Pune"], aggregation_paths=None, short_code="cli1",
                                    )

        self.data_record_id = self.entity.add_data(data=[("Name", "Ruby", self.name_type)],
                                                   submission=dict(submission_id="1"))

        self.reporter = create_entity(self.dbm, entity_type=["reporter"],
                                      location=["India", "Pune"], aggregation_paths=None, short_code="rep1",
                                      )

        self.reporter.add_data(data=[(MOBILE_NUMBER_FIELD, '1234', self.telephone_number_type),
            (NAME_FIELD, "Test_reporter", self.name_type)], submission=dict(submission_id="2"))

        question1 = TextField(name="entity_question", code="EID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=self.entity_id_type)
        question2 = TextField(name="Name", code="NAME", label="Clinic Name",
                              defaultValue="some default value", language="eng",
                              constraints=[TextLengthConstraint(4, 15)],
                              ddtype=self.name_type, required=False)
        question3 = IntegerField(name="Arv stock", code="ARV", label="ARV Stock",
                                 constraints=[NumericRangeConstraint(min=15, max=120)], ddtype=self.stock_type, required=False)
        question4 = SelectField(name="Color", code="COL", label="Color",
                                options=[("RED", 1), ("YELLOW", 2)], ddtype=self.color_type, required=False)

        self.form_model = FormModel(self.dbm, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                    form_code="clinic", type='survey', fields=[question1, question2, question3])
        self.form_model.add_field(question4)
        self.form_model__id = self.form_model.save()

        self.submission_handler = None
        self.sms_player = SMSPlayer(self.dbm, LocationTree())

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def send_sms(self, text):
        transport_info = TransportInfo(transport="sms", source="1234", destination="5678")
        response = self.sms_player.accept(Request(transportInfo=transport_info, message=text))
        return response

    def test_should_save_submitted_sms(self):
        text = "clinic .EID %s .name CLINIC-MADA .ARV 50 .COL a" % self.entity.short_code

        response = self.send_sms(text)

        self.assertTrue(response.success)

        data_record_id = response.datarecord_id
        data_record = self.dbm._load_document(id=data_record_id, document_class=DataRecordDocument)
        self.assertEqual(self.name_type.slug, data_record.data["Name"]["type"]["slug"])
        self.assertEqual(self.stock_type.slug, data_record.data["Arv stock"]["type"]["slug"])
        self.assertEqual(self.color_type.slug, data_record.data["Color"]["type"]["slug"])
        self.assertEqual("clinic", data_record.submission['form_code'])
        self.assertEqual(u"Test_reporter", response.reporters[0].get(NAME_FIELD))

        data = self.entity.values({"Name": "latest", "Arv stock": "latest", "Color": "latest"})
        self.assertEquals(data["Arv stock"], 50)
        self.assertEquals(data["Name"], "CLINIC-MADA")

    def test_should_save_submitted_sms_for_activity_report(self):
        question1 = TextField(name="entity_question", code="EID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=self.entity_id_type)
        question2 = TextField(name="Name", code="NAME", label="Clinic Name",
                              defaultValue="some default value", language="eng",
                              constraints=[TextLengthConstraint(4, 15)],
                              ddtype=self.name_type)
        question3 = IntegerField(name="Arv stock", code="ARV", label="ARV Stock",
                                 constraints=[NumericRangeConstraint(min=15, max=120)], ddtype=self.stock_type)
        activity_report = FormModel(self.dbm, entity_type=["reporter"], name="report", label="reporting form_model",
                                    form_code="acp", type='survey', fields=[question1, question2, question3])
        activity_report.save()

        text = "acp .name tester .ARV 50 "

        response = self.send_sms(text)

        self.assertTrue(response.success)
        self.assertEqual(u"Test_reporter", response.reporters[0].get(NAME_FIELD))

        data_record_id = response.datarecord_id
        data_record = self.dbm._load_document(id=data_record_id, document_class=DataRecordDocument)
        self.assertEqual(self.name_type.slug, data_record.data["Name"]["type"]["slug"])
        self.assertEqual(self.stock_type.slug, data_record.data["Arv stock"]["type"]["slug"])
        self.assertEqual("acp", data_record.submission['form_code'])
        data = self.reporter.values({"Name": "latest", "Arv stock": "latest"})
        self.assertEquals(data["Arv stock"], 50)
        self.assertEquals(data["Name"], "tester")

    def test_should_give_error_for_wrong_integer_value(self):
        text = "clinic .EID %s .ARV 150 " % self.entity.id
        response = self.send_sms(text)
        self.assertFalse(response.success)
        self.assertEqual(len(response.errors), 1)

    def test_should_give_error_for_wrong_text_value(self):
        text = "clinic .EID CID001 .NAME ABC"

        response = self.send_sms(text)
        self.assertFalse(response.success)
        self.assertEqual(len(response.errors), 1)

    def test_get_submissions_for_form(self):
        self.dbm._save_document(SubmissionLogDocument(channel="transport", source=1234,
                                                      destination=12345, form_code="abc",
                                                      values={'Q1': 'ans1', 'Q2': 'ans2'},
                                                      status=False, error_message="", data_record_id='2345678'))
        self.dbm._save_document(SubmissionLogDocument(channel="transport", source=1234,
                                                      destination=12345, form_code="abc",
                                                      values={'Q1': 'ans12', 'Q2': 'ans22'},
                                                      status=False, error_message="", data_record_id='1234567'))
        self.dbm._save_document(SubmissionLogDocument(channel="transport", source=1234,
                                                      destination=12345, form_code="def",
                                                      values={'defQ1': 'defans12', 'defQ2': 'defans22'},
                                                      status=False, error_message="", data_record_id='345678'))

        oneDay = datetime.timedelta(days=1)
        tomorrow = datetime.datetime.now() + oneDay
        submissions = get_submissions(self.dbm, "abc", 0, int(mktime(tomorrow.timetuple())) * 1000)
        self.assertEquals(2, len(submissions))
        self.assertEquals({'Q1': 'ans12', 'Q2': 'ans22'}, submissions[0].values)
        self.assertEquals({'Q1': 'ans1', 'Q2': 'ans2'}, submissions[1].values)

    def test_error_messages_are_being_logged_in_submissions(self):
        text = "clinic .EID %s .ARV 150 " % self.entity.id
        self.send_sms(text)
        oneDay = datetime.timedelta(days=1)
        tomorrow = datetime.datetime.now() + oneDay
        submissions= get_submissions(self.dbm, "clinic", 0, int(mktime(tomorrow.timetuple())) * 1000)
        self.assertEquals(1, len(submissions))
        self.assertEquals(u"Answer 150 for question ARV is greater than allowed.", submissions[0].errors)


    def test_should_register_new_entity(self):
        message1 = """reg .t  dog .n  Clinic in Diégo–Suarez .l  Diégo–Suarez .g  -12.35  49.3  .d This is a Clinic in
        Diégo–Suarez . m
        87654325
        """
        response = self.send_sms(message1)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = "dog1"
        self.assertEqual(response.short_code, expected_short_code)
        a = get_by_short_code(self.dbm, expected_short_code, ["dog"])
        self.assertEqual(a.short_code, expected_short_code)

        text = "reg .N buddy .S bud .T dog .G 80 80 .D its a dog! .M 45557"

        response = self.send_sms(text)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        self.assertEqual(response.short_code, "bud", ["dog"])
        a = get_by_short_code(self.dbm, "bud", ["dog"])
        self.assertEqual(a.short_code, "bud")

        text = "reg .N buddy2 .T dog .L 80 80 .D its another dog! .M 78541"

        response = self.send_sms(text)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = "dog3"
        self.assertEqual(response.short_code, expected_short_code)
        b = get_by_short_code(self.dbm, expected_short_code, ["dog"])
        self.assertEqual(b.short_code, expected_short_code)

    def test_should_return_error_for_registration_having_invalid_geo_data(self):
        INVALID_LATITUDE = 380
        text = "reg .N buddy2 .T dog .G %s 80 .D its another dog! .M 78541" % (INVALID_LATITUDE,)

        response = self.send_sms(text)
        self.assertFalse(response.success)
        self.assertEqual({'g': 'The answer 380 must be between -90 and 90'}, response.errors)

        INVALID_LONGITUDE = -184
        text = "reg .N buddy2 .T dog .G 80 %s .D its another dog! .M 78541" % (INVALID_LONGITUDE,)

        response = self.send_sms(text)
        self.assertFalse(response.success)
        self.assertEqual({'g': 'The answer -184 must be between -180 and 180'}, response.errors)

    def test_should_log_submission(self):
        transport_info = TransportInfo(transport="sms", source="1234", destination="5678")
        request = Request(transportInfo=transport_info, message="reg .N buddy .S DOG3 .T dog .G 1 1")

        response = self.sms_player.accept(request)
        submission_log = self.dbm._load_document(response.submission_id, SubmissionLogDocument)
        self.assertIsInstance(submission_log, SubmissionLogDocument)
        self.assertEquals(transport_info.transport, submission_log.channel)
        self.assertEquals(transport_info.source, submission_log.source)
        self.assertEquals(transport_info.destination, submission_log.destination)
        self.assertEquals(True, submission_log. status)
        self.assertEquals("reg", submission_log.form_code)
        self.assertEquals({'n': 'buddy', 's': 'DOG3', 't': 'dog', 'g': '1 1'}, submission_log.values)
        self.assertEquals(transport_info.destination, submission_log.destination)
        self.assertEquals(response.datarecord_id, submission_log.data_record_id)


    def test_should_throw_error_if_entity_with_same_short_code_exists(self):
        text = "reg .N buddy .S DOG3 .T dog .G 80 80 .D its a dog! .M 123456"
        self.send_sms(text)
        text = "reg .N buddy2 .S dog3 .T dog .L 80 80 .D its a dog! .M 123456"
        with self.assertRaises(DataObjectAlreadyExists):
            self.send_sms(text)

    def test_should_throw_error_if_reporter_with_same_phone_number_exists(self):
        text = "reg .N buddy .T reporter .G 80 80 .M 123456"
        self.send_sms(text)
        with self.assertRaises(MultipleReportersForANumberException):
            text = "reg .N buddy2 .T reporter .L 80 80 .M 123456"
            self.send_sms(text)

    def test_should_throw_error_if_mobile_phone_is_in_weird_pattern(self):
        text = "reg .N buddy .T reporter .G 80 80 .M 1234@5678"
        response = self.send_sms(text)
        self.assertFalse(response.success)
        self.assertTrue(response.errors.get('m') is not None)

    def test_should_throw_error_if_mobile_phone_is_too_long(self):
        text = "reg .N buddy .T reporter .G 80 80 .M 1234567889898989898989812312"
        response = self.send_sms(text)
        assert(response.success is False)
        self.assertTrue(response.errors.get('m') is not None)

    def test_should_throw_error_if_reporter_registration_submission_has_no_mobile_number(self):
        with self.assertRaises(MobileNumberMissing):
            text = "reg .N buddy2 .T reporter .L 80 80"
            self.send_sms(text)

    def test_should_throw_error_if_entityType_doesnt_exist(self):
        with self.assertRaises(EntityTypeDoesNotExistsException):
            text = "reg .N buddy1 .S DOG3 .T cat .L 80 80 .D its another dog! .M 1234567"
            self.send_sms(text)

    def test_entity_instance_is_case_insensitive(self):
        text = "clinic .EID %s .name CLINIC-MADA .ARV 50 .COL a" % "CLI1"

        response = self.send_sms(text)

        self.assertTrue(response.success)

    def test_questionnaire_code_is_case_insensitive(self):
        text = "CLINIC .EID %s .name CLINIC-MADA .ARV 50 .COL a" % "cli1"
        response = self.send_sms(text)
        self.assertTrue(response.success)

    def test_entity_type_is_case_insensitive_in_registration(self):
        text = "reg .n buddy .T DOG .G 80 80 .M 123456"
        response = self.send_sms(text)
        self.assertTrue(response.success)
        data_record = self.dbm._load_document(response.datarecord_id, DataRecordDocument)
        actual_type = data_record["entity"]["aggregation_paths"]["_type"]
        self.assertEquals(["dog"], actual_type)

    def test_should_accept_unicode_submissions(self):
        text = "reg .s Āgra .n Agra .m 080 .t clinic .g 45 56"
        with self.assertRaises(EntityTypeDoesNotExistsException):
            self.send_sms(text)

    def test_should_accept_unicode_submissions_and_invalidate_wrong_GPS(self):
        text = "reg .s Āgra .n Agra .m 080 .t clinic .g 45Ö 56"
        with self.assertRaises(GeoCodeFormatException):
            self.send_sms(text)

    def test_should_raise_exception_for_inactive_form_model(self):
        self.form_model.deactivate()
        self.form_model.save()
        text = "clinic .EID %s .name CLINIC-MADA .ARV 50 .COL a" % self.entity.short_code
        with self.assertRaises(InactiveFormModelException):
            self.send_sms(text)

    def test_should_set_submission_log_as_Test_for_form_model_in_test_mode(self):
        self.form_model.set_test_mode()
        self.form_model.save()
        text = "clinic .EID %s .name CLINIC-MADA .ARV 50 .COL a" % self.entity.short_code
        response = self.send_sms(text)

        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        self.assertIsNotNone(response.submission_id)
        submission_log = self.dbm._load_document(response.submission_id, SubmissionLogDocument)
        self.assertTrue(submission_log.test)


    def test_should_register_entity_with_geo_code(self):
        message1 = """reg .t dog .n Dog in Diégo–Suarez .g -12.35  49.3  .d This is a Dog in
        Diégo–Suarez . m
        87654325
        """
        response = self.send_sms(message1)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = 'dog1'
        self.assertEqual(response.short_code, expected_short_code)
        dog = get_by_short_code(self.dbm, expected_short_code, ["dog"])
        self.assertEqual([-12.35, 49.3], dog.geometry.get("coordinates"))

    def test_should_register_entity_with_geocode_if_only_location_provided(self):
        message1 = """reg .t dog .n Dog in AMPIZARANTANY .l AMPIZARANTANY .d This is a Dog in
        AMPIZARANTANY . m
        87654325
        """
        response = self.send_sms(message1)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = 'dog1'
        self.assertEqual(response.short_code, expected_short_code)
        dog = get_by_short_code(self.dbm, expected_short_code, ["dog"])
        self.assertEqual([-12, 60], dog.geometry.get("coordinates"))

    def test_should_register_entity_with_geocode_and_location_provided(self):
        message1 = """reg .t dog .n Dog in AMPIZARANTANY .l AMPIZARANTANY .g 10 10 .d This is a Dog in
        AMPIZARANTANY . m
        87654325
        """
        response = self.send_sms(message1)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = 'dog1'
        self.assertEqual(response.short_code, expected_short_code)
        dog = get_by_short_code(self.dbm, expected_short_code, ["dog"])
        self.assertEqual([10, 10], dog.geometry.get("coordinates"))
        self.assertEqual(["ampizarantany"], dog.location_path)

    def test_get_submissions_for_form_for_an_activity_period(self):
        self.dbm._save_document(SubmissionLogDocument(channel="transport", source=1234,
                                                      destination=12345, form_code="abc",
                                                      values={'Q1': 'ans1', 'Q2': 'ans2'},
                                                      status=False, error_message="", data_record_id='2345678',event_time=datetime.datetime(2011,9,1)))
        self.dbm._save_document(SubmissionLogDocument(channel="transport", source=1234,
                                                      destination=12345, form_code="abc",
                                                      values={'Q1': 'ans12', 'Q2': 'ans22'},
                                                      status=False, error_message="", data_record_id='1234567',event_time=datetime.datetime(2011,3,3)))
        self.dbm._save_document(SubmissionLogDocument(channel="transport", source=1234,
                                                      destination=12345, form_code="abc",
                                                      values={'Q1': 'ans12', 'Q2': 'defans22'},
                                                      status=False, error_message="", data_record_id='345678',event_time=datetime.datetime(2011,3,10)))

        from_time = datetime.datetime(2011,3,1)
        end_time = datetime.datetime(2011,3,30)

        submissions = get_submissions_for_activity_period(self.dbm, "abc", from_time, end_time)
        self.assertEquals(2, len(submissions))
