# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager, remove_db_manager
from mangrove.datastore.entity import define_type
from mangrove.datastore.field import SelectField, IntegerField, TextField
from mangrove.datastore.form_model import FormModel
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, FieldDoesNotExistsException
import smsplayer
import mangrove.datastore.datarecord as datarecord
from mangrove.datastore.datadict import DataDictType

class TestSmsPlayer(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        remove_db_manager(self.dbm)
        self.dbm = get_db_manager(database='mangrove-test')
        self.name_type = DataDictType(self.dbm, name='First name', slug='Name', primitive_type='string')
        self.name_type.save()
        self.entity = define_type(self.dbm, ["HealthFacility", "Clinic"])
        self.entity_instance = datarecord.register(self.dbm, entity_type="HealthFacility.Clinic",
                                                   data=[("Name", "Ruby", self.name_type)],
                                                   location=["India", "Pune"], source="sms")
        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity"
                              , language="eng", entity_question_flag=True)
        question2 = TextField(name="question1_Name", question_code="Q1", label="What is your name",
                              defaultValue="some default value", language="eng")
        question3 = IntegerField(name="Father's age", question_code="Q2", label="What is your Father's Age",
                                 range={"min": 15, "max": 120})
        question4 = SelectField(name="Color", question_code="Q3", label="What is your favourite color",
                                options=[("RED", 1), ("YELLOW", 2)])

        self.form_model = FormModel(self.dbm, entity_type_id=self.entity.id, name="aids", label="Aids form_model",
                                    form_code="1", type='survey', fields=[
                        question1, question2,question3])
        self.form_model.add_question(question4)
        self.form_model__id = self.form_model.save()

    def tearDown(self):
        del self.dbm.database[self.form_model__id]
        _delete_db_and_remove_db_manager(self.dbm)
        pass


    def test_should_submit_sms(self):
        # TODO: fix this for new datarecord structure
        #text = "1 +ID %s +Q1 akshay +Q2 50 +Q3 2 "%self.entity_instance.id
        #submission_id = smsplayer.sumbit(dbm=self.dbm, text=text, from_number=23456, to_number=12345)
        #self.assertIsNotNone(submission_id)
        pass

    def test_should_reject_if_questionnaire_does_not_exist(self):
        text = "2 +ID %s +Q1 akshay +Q2 50 +Q3 2 "%self.entity_instance.id
        message = ""
        try:
            smsplayer.sumbit(dbm=self.dbm, text=text, from_number=23456, to_number=12345)
        except FormModelDoesNotExistsException as ex:
            message = ex.message
        self.assertEquals(message, "The questionnaire with code 2 does not exists")

    def test_should_reject_if_question_does_not_exist(self):
        text = "1 +ID %s +Q1 akshay +Non_existing_Question 50 +Q3 2"%self.entity_instance.id
        message = ""
        try:
            smsplayer.sumbit(dbm=self.dbm,text=text,from_number=23456,to_number=12345)
        except FieldDoesNotExistsException as ex:
            message = ex.message
        self.assertEquals(message,"The field with code Non_existing_Question does not exists")