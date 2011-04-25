# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager, remove_db_manager
from mangrove.datastore.entity import define_type
from mangrove.datastore.field import SelectField, IntegerField, TextField
from mangrove.datastore.form_model import FormModel
from mangrove.errors.MangroveException import FormModelDoesNotExistsException
import smsplayer
import mangrove.datastore.datarecord as datarecord


class TestSmsPlayer(unittest.TestCase):

    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        remove_db_manager(self.dbm)
        self.dbm = get_db_manager(database='mangrove-test')
        self.entity = define_type(self.dbm, ["HealthFacility", "Clinic"])
        self.entity_instance = datarecord.register(self.dbm,entity_type = "HealthFacility.Clinic", data=[("Name", "Ruby",)], location= ["India", "Pune"], source="sms")
        question1 = TextField(name="question1_Name", question_code="Q1", label="What is your name",
                                 defaultValue="some default value", language="eng")
        question2 = IntegerField(name="Father's age", question_code="Q2", label="What is your Father's Age",
                                    range={"min": 15, "max": 120})
        question3 = SelectField(name="Color", question_code="Q3", label="What is your favourite color",
                                   options=[("RED", 1), ("YELLOW", 2)])

        self.form_model = FormModel(self.dbm, entity_id=self.entity.id, name="aids", label="Aids form_model",
                                    form_code="1", type='survey', fields=[
                    question1, question2])
        self.form_model.add_question(question3)
        self.form_model__id = self.form_model.save()

    def tearDown(self):
        del self.dbm.database[self.form_model__id]
        _delete_db_and_remove_db_manager(self.dbm)
        pass


    def test_should_submit_sms(self):
        text = "1 +Q1 akshay +Q2 50 +Q3 2 "
        submission_id = smsplayer.sumbit(dbm=self.dbm, text=text, from_number=23456, to_number=12345,
                                         entity_id=self.entity_instance.id)
        self.assertIsNotNone(submission_id)

    def test_should_reject_if_questionnaire_does_not_exist(self):
        text = "2 +Q1 akshay +Q2 50 +Q3 2 "
        message = ""
        try:
            smsplayer.sumbit(dbm=self.dbm,text=text,from_number=23456,to_number=12345,entity_id=self.entity_instance.id)
        except FormModelDoesNotExistsException as ex:
            message = ex.message
        self.assertEquals(message,"The questionnaire with code 2 does not exists")

#    def test_should_reject_if_question_does_not_exist(self):
#        text = "1 +Q1 akshay +Non_existing_Question 50 +Q3 2 "
#        response = smsplayer.sumbit(dbm=self.dbm,text=text,from_number=23456,to_number=12345,entity_id=self.entity_instance.id)
#        self.assertEquals(response,"Reject")