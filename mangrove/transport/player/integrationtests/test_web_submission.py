#vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

#  This is an integration test.
# Send message via web, parse them and save.

from mangrove.bootstrap import initializer
from mangrove.datastore.documents import  DataRecordDocument
from mangrove.datastore.entity import get_by_short_code, create_entity
from mangrove.datastore.entity_type import define_type
from mangrove.errors.MangroveException import  DataObjectAlreadyExists, EntityTypeDoesNotExistsException

from mangrove.form_model.field import TextField, IntegerField, SelectField, ShortCodeField
from mangrove.form_model.form_model import FormModel, MOBILE_NUMBER_FIELD_CODE, EntityFormModel
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint
from mangrove.transport.player.player import WebPlayer
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.transport.contract.transport_info import TransportInfo
from mangrove.transport.contract.request import Request

class TestWEBSubmission(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)
        initializer.run(self.manager)
        define_type(self.manager, ["dog"])
        self.entity_type = ["clinic"]
        define_type(self.manager, self.entity_type)

        self.entity = create_entity(self.manager, entity_type=self.entity_type,
                                    location=["India", "Pune"], aggregation_paths=None, short_code="cli1",
                                    )
        self.entity.save()
        #Form Model with unique id question
        question1 = ShortCodeField(name="entity_question", code="EID", label="What is associated entity")
        question2 = TextField(name="Name", code="NAME", label="Clinic Name",
                              defaultValue="some default value",
                              constraints=[TextLengthConstraint(4, 15)], required=False)
        question3 = IntegerField(name="Arv stock", code="ARV", label="ARV Stock",
                                 constraints=[NumericRangeConstraint(min=15, max=120)], required=False)
        question4 = SelectField(name="Color", code="COL", label="Color",
                                options=[("RED", 'a'), ("YELLOW", 'b')], required=False)
        self.form_model = EntityFormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                    form_code="clinic",  fields=[question1, question2, question3, question4], is_registration_model=True)
        self.form_model.save()

        self.web_player = WebPlayer(self.manager, location_tree=LocationTree())

    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def send_request_to_web_player(self, text):
        transport_info = TransportInfo(transport="web", source="tester150411@gmail.com", destination="")
        response = self.web_player.accept(Request(message=text, transportInfo=transport_info))
        return response


    def test_should_save_submitted_form_for_activity_report(self):
        text = {'form_code':'reg', 'n':'name','l':'location','m':'768686' ,'t':'reporter'}
        response = self.send_request_to_web_player(text)
        self.assertTrue(response.success)

        data_record_id = response.datarecord_id
        data_record = self.manager._load_document(id=data_record_id, document_class=DataRecordDocument)
        self.assertEqual("reg", data_record.submission['form_code'])

    def test_should_give_error_for_wrong_integer_value(self):
        text = {'form_code': 'clinic', 'EID':self.entity.short_code, 'ARV': '150'}
        response = self.send_request_to_web_player(text)
        self.assertFalse(response.success)
        self.assertEqual(len(response.errors), 1)
        self.assertEqual(u'Answer 150 for question ARV is greater than allowed.',response.errors.get('ARV'))

    def test_should_give_error_for_wrong_text_value(self):
        text = {'form_code': 'clinic', 'EID': 'CID001', 'NAME': 'ABC'}
        response = self.send_request_to_web_player(text)
        self.assertFalse(response.success)
        self.assertEqual(len(response.errors), 1)
        self.assertEqual(u'Answer ABC for question NAME is shorter than allowed.',response.errors.get('NAME'))


    def test_should_register_new_entity_and_generate_short_code_if_not_given(self):
        text = {'form_code':'reg', 't': 'dog', 'n': 'Diégo–Suarez', 'l': 'Diégo–Suarez', 'g': '-12.35  49.3', 'd': 'This is a Clinic in Diégo–Suarez', 'm': '87654325'}
        response = self.send_request_to_web_player(text)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = "dog1"
        self.assertEqual(response.short_code, expected_short_code)
        a = get_by_short_code(self.manager, expected_short_code, ["dog"])
        self.assertEqual(a.short_code, expected_short_code)

        text = {'form_code':'reg', 's':'bud', 'n':'buddy', 't': 'dog', 'l': 'Diégo–Suarez', 'g': '-12.35  49.3', 'd':'its a dog!', 'm': '45557'}
        response = self.send_request_to_web_player(text)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = "bud"
        self.assertEqual(response.short_code, expected_short_code)
        a = get_by_short_code(self.manager, "bud", ["dog"])
        self.assertEqual(a.short_code, "bud")

        text = {'form_code':'reg', 'n':'buddy2', 't': 'dog', 'l': 'Diégo–Suarez', 'g': '-12.35  49.3', 'd':'its another dog!', 'm': '745557'}
        response = self.send_request_to_web_player(text)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = "dog3"
        self.assertEqual(response.short_code, expected_short_code)
        b = get_by_short_code(self.manager, expected_short_code, ["dog"])
        self.assertEqual(b.short_code, expected_short_code)

    def test_should_return_error_for_registration_having_invalid_geo_data(self):
        INVALID_GEOCODE = '38'
        INVALID_LATITUDE = '380 30'
        INVALID_LONGITUDE = '30 -184'

        text = {'form_code':'reg', 'N':'buddy2', 'S':'bud', 'T': 'dog', 'g':INVALID_GEOCODE, 'D':'its another dog!', 'M': '745557'}
        response = self.send_request_to_web_player(text)
        self.assertFalse(response.success)
        self.assertEqual({'g': u'Incorrect GPS format. The GPS coordinates must be in the following format: xx.xxxx,yy.yyyy. Example -18.8665,47.5315'}, response.errors)
        
        text = {'form_code':'reg', 'N':'buddy2', 'S':'bud', 'T': 'dog', 'g':INVALID_LATITUDE, 'D':'its another dog!', 'M': '745557'}
        response = self.send_request_to_web_player(text)
        self.assertFalse(response.success)
        self.assertEqual({'g': u'Invalid GPS value.'}, response.errors)

        text = {'form_code':'reg', 'N':'buddy2', 'S':'bud', 'T': 'dog', 'g':INVALID_LONGITUDE, 'D':'its another dog!', 'M': '745557'}
        response = self.send_request_to_web_player(text)
        self.assertFalse(response.success)
        self.assertEqual({'g': u'Invalid GPS value.'}, response.errors)

    def test_should_throw_error_if_entity_with_same_short_code_exists(self):
        text = {'form_code':'reg', 'n':'buddy', 's':'dog3', 't': 'dog', 'g':'80 80', 'd':'its a dog!', 'm':'12345'}
        self.send_request_to_web_player(text)

        text = {'form_code':'reg', 'n':'buddy2', 's':'dog3', 't': 'dog', 'g':'80 80', 'd':'its a dog!', 'm':'123456'}
        with self.assertRaises(DataObjectAlreadyExists):
            self.send_request_to_web_player(text)

    def test_should_throw_error_if_reporter_with_same_phone_number_exists(self):
        text = {'form_code':'reg', 'n':'buddy', 't': 'reporter', 'g':'80 80', 'm':'12345'}
        response = self.send_request_to_web_player(text)
        self.assertTrue(response.success)

        text = {'form_code':'reg', 'n':'buddy2', 't': 'reporter', 'g':'80 80', 'm':'12345'}
        response = self.send_request_to_web_player(text)
        self.assertFalse(response.success)
        self.assertTrue('m' in response.errors)

    def test_should_throw_error_if_mobile_phone_is_too_long(self):
        text = {'form_code':'reg', 'n':'buddy', 't': 'reporter', 'g':'80 80', 'm':'1234534673498723909872373267'}
        response = self.send_request_to_web_player(text)
        self.assertFalse(response.success)
        self.assertTrue("Answer 1234534673498723925129953280 for question m is longer than allowed.", response.errors.get('m'))

    def test_should_throw_error_if_reporter_registration_submission_has_no_mobile_number(self):
        text = {'form_code':'reg', 'n':'buddy', 't': 'reporter', 'g':'80 80'}
        response = self.send_request_to_web_player(text)
        self.assertFalse(response.success)
        self.assertTrue(MOBILE_NUMBER_FIELD_CODE in response.errors)

    def test_should_throw_error_if_entityType_doesnt_exist(self):
        with self.assertRaises(EntityTypeDoesNotExistsException):
            text = {'form_code':'reg', 'n':'buddy', 's':'dog3', 't': 'cat', 'g':'80 80', 'd':'Its another dog', 'm':'123456'}
            self.send_request_to_web_player(text)

    def test_entity_instance_is_case_insensitive(self):
        with self.assertRaises(DataObjectAlreadyExists):
            text = {'form_code':'clinic', 'EID':'CLI1', 'NAME': 'CLINIC-MADA', 'ARV': '50', 'COL': ['b']}
            self.send_request_to_web_player(text)

    def test_entity_type_is_case_insensitive_in_registration(self):
        text = {'form_code':'reg', 'n':'buddy', 't': 'DOG', 'g':'80 80', 'm':'123456'}
        response = self.send_request_to_web_player(text)
        self.assertTrue(response.success)
        self.assertEquals(["dog"], response.entity_type)

    def test_should_accept_unicode_submissions_and_able_to_invalidate_wrong_GPS(self):
        text = {'form_code':'reg', 'n':'Agra', 't': 'clinic', 'g':'480 80', 'm':'08045'}
        response = self.send_request_to_web_player(text)
        self.assertFalse(response.success)
        self.assertEquals(u'Invalid GPS value.', response.errors.get('g'))
        self.assertIsNone(response.errors.get('m'))

    def test_should_register_entity_with_geo_code(self):
        text = {'form_code':'reg', 'n':'Diégo–Suarez', 't': 'dog', 'g':'-12.35 49.3', 'd':'This is a dog in Diégo–Suarez','m':'786780'}
        response = self.send_request_to_web_player(text)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = 'dog1'
        self.assertEqual(response.short_code, expected_short_code)
        dog = get_by_short_code(self.manager, expected_short_code, ["dog"])
        self.assertEqual([-12.35, 49.3], dog.geometry.get("coordinates"))

    def test_should_register_entity_with_geocode_if_only_location_provided(self):
        text = {'form_code':'reg', 'n':'Dog in AMPIZARANTANY', 't': 'dog', 'l':'AMPIZARANTANY', 'd':'This is a dog in Diégo–Suarez','m':'786780'}
        response = self.send_request_to_web_player(text)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = 'dog1'
        self.assertEqual(response.short_code, expected_short_code)
        dog = get_by_short_code(self.manager, expected_short_code, ["dog"])
        self.assertEqual([-12, 60], dog.geometry.get("coordinates"))

    def test_should_register_entity_with_geocode_and_location_provided(self):
        text = {'form_code':'reg', 'n':'Dog in AMPIZARANTANY', 't': 'dog', 'l':'AMPIZARANTANY', 'g':'10 10','d':'This is a dog in Diégo–Suarez','m':'786780'}
        response = self.send_request_to_web_player(text)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        expected_short_code = 'dog1'
        self.assertEqual(response.short_code, expected_short_code)
        dog = get_by_short_code(self.manager, expected_short_code, ["dog"])
        self.assertEqual([10, 10], dog.geometry.get("coordinates"))
        self.assertEqual([u'arantany'], dog.location_path)

class LocationTree(object):
    def get_location_hierarchy_for_geocode(self, lat, long ):
        return ['madagascar']

    def get_centroid(self, location_name, level):
        return 60, -12

    def get_location_hierarchy(self,lowest_level_location_name):
        return [u'arantany']
