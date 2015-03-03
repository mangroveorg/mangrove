#vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


#  This is an integration test.
# Send sms, parse and save.
import random
from string import upper
from time import mktime
import unittest
import datetime
from couchdb.design import ViewDefinition
from mangrove.bootstrap import initializer
from mangrove.bootstrap.views import view_js
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.documents import DataRecordDocument
from mangrove.datastore.entity import get_by_short_code, create_entity, create_contact
from mangrove.errors.MangroveException import  DataObjectAlreadyExists, EntityTypeDoesNotExistsException,\
 DataObjectNotFound, FormModelDoesNotExistsException
from mangrove.form_model.field import TextField, IntegerField, SelectField, ShortCodeField
from mangrove.form_model.form_model import FormModel, NAME_FIELD, MOBILE_NUMBER_FIELD, MOBILE_NUMBER_FIELD_CODE,\
SHORT_CODE, ENTITY_TYPE_FIELD_CODE, get_form_model_by_code,EntityFormModel
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint
from mangrove.utils.test_utils.database_utils import safe_define_type, uniq, ut_reporter_id
from mangrove.transport.player.player import SMSPlayer
from mangrove.transport.contract.transport_info import TransportInfo
from mangrove.transport.contract.request import Request
from mangrove.datastore.cache_manager import get_cache_manager

class LocationTree(object):
    def get_location_hierarchy_for_geocode(self, lat, long ):
        return ['madagascar']

    def get_centroid(self, location_name, level):
        return 60, -12

    def get_location_hierarchy(self, lowest_level_location_name):
        return [u'arantany']

FORM_CODE = "abc"


def create_db(name):
    dbm = get_db_manager('http://localhost:5984/', name)
    views = []
    for v in view_js.keys():
        funcs = view_js[v]
        map = (funcs['map'] if 'map' in funcs else None)
        reduce = (funcs['reduce'] if 'reduce' in funcs else None)
        views.append(ViewDefinition(v, v, map, reduce))

    ViewDefinition.sync_many(dbm.database, views)
    return dbm


class TestShouldSaveSMSSubmission(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dbm = create_db(uniq('mangrove-test'))
        initializer.initial_data_setup(cls.dbm)
        cls.entity_type = ["healthfacility", "clinic"]
        safe_define_type(cls.dbm, cls.entity_type)

        cls.entity_short_code = "cli" + str(int(random.random()*10000))
        cls.entity = create_entity(cls.dbm, entity_type=cls.entity_type,
            location=["India", "Pune"], aggregation_paths=None, short_code=cls.entity_short_code,
        )
        cls.entity.save()
        cls.reporter_id = "rep" + str(int(random.random()*10000))
        cls.reporter = create_contact(cls.dbm, location=["India", "Pune"],
                                      aggregation_paths=None, short_code=cls.reporter_id)
        cls.reporter.save()

        cls.phone_number = str(int(random.random() * 10000000))
        cls.reporter.add_data(data=[(MOBILE_NUMBER_FIELD, cls.phone_number),
            (NAME_FIELD, "Test_reporter")], submission=dict(submission_id="2"))

        question1 = ShortCodeField(name="entity_question", code="EID", label="What is associated entity",constraints=[TextLengthConstraint(min=1, max=20)])
        question2 = TextField(name="Name", code="NAME", label="Clinic Name",
            defaultValue="some default value",
            constraints=[TextLengthConstraint(4, 15)], required=False)
        question3 = IntegerField(name="Arv stock", code="ARV", label="ARV Stock",
            constraints=[NumericRangeConstraint(min=15, max=120)], required=False)
        question4 = SelectField(name="Color", code="COL", label="Color",
            options=[("RED", 'a'), ("YELLOW", 'a')], required=False)

        try:
            cls.form_model = get_form_model_by_code(cls.dbm, "clinic")
        except FormModelDoesNotExistsException:
            cls.form_model = EntityFormModel(cls.dbm, entity_type=cls.entity_type, name="aids", label="Aids form_model",
                form_code="clinic",  fields=[question1, question2, question3], is_registration_model=True)
            cls.form_model.add_field(question4)
            cls.form_model.save()
        cls.sms_player = SMSPlayer(cls.dbm, LocationTree())
        cls.sms_ordered_message_player = SMSPlayer(cls.dbm, LocationTree())

    @classmethod
    def tearDownClass(cls):
        _delete_db_and_remove_db_manager(cls.dbm)
        get_cache_manager().flush_all()

    def send_sms(self,text, player = None):
        player = player or self.sms_player
        transport_info = TransportInfo(transport="sms", source=self.phone_number, destination="5678")
        response = player.accept(Request(message=text, transportInfo=transport_info))
        return response

    def test_should_give_error_for_wrong_integer_value(self):
        text = "clinic .EID %s .ARV 150 " % self.entity.short_code
        response = self.send_sms(text)
        self.assertFalse(response.success)
        self.assertEqual(len(response.errors), 1)

    def test_should_give_error_for_wrong_text_value(self):
        text = "clinic .EID %s .NAME ABC" % self.entity.short_code

        response = self.send_sms(text)
        self.assertFalse(response.success)
        self.assertEqual(len(response.errors), 1)

    def test_entity_id_with_more_than_20_chars_for_submission(self):
        response = self.send_sms("clinic 012345678901234567891", self.sms_ordered_message_player)
        self.assertEqual("Answer 012345678901234567891 for question EID is longer than allowed.",
                         response.errors['EID'])
