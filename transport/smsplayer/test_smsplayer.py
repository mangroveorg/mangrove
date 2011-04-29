# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager, remove_db_manager
from mangrove.datastore.entity import define_type
from mangrove.datastore.field import SelectField, IntegerField, TextField
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, FieldDoesNotExistsException, NumberNotRegisteredException
from mangrove.form_model.form_model import FormModel
import smsplayer
import mangrove.datastore.datarecord as datarecord


class TestSmsPlayer(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        remove_db_manager(self.dbm)
        self.dbm = get_db_manager(database='mangrove-test')
        self.entity = define_type(self.dbm, ["HealthFacility", "Clinic"])
        self.reporter = define_type(self.dbm, ["Reporter"])
        self.entity_instance = datarecord.register(self.dbm, entity_type="HealthFacility.Clinic",
                                                   data=[("Name", "Ruby",)], location=["India", "Pune"], source="sms")
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
                    question1, question2, question3])
        self.form_model.add_field(question4)
        self.form_model__id = self.form_model.save()
        datarecord.register(self.dbm, entity_type=["Reporter"], data=[("telephone_number", 1234567),("first_name","Test_reporter")], location=[],
                            source="sms")
        datarecord.register(self.dbm, entity_type=["Reporter"], data=[("telephone_number", 12345)], location=[],
                            source="sms")

    def tearDown(self):
        del self.dbm.database[self.form_model__id]
        _delete_db_and_remove_db_manager(self.dbm)
        pass


    def test_should_submit_sms(self):
        text = "1 +ID %s +Q1 akshay +Q2 50 +Q3 2 " % self.entity_instance.id
        submission_id = smsplayer.submit(dbm=self.dbm, text=text, from_number=1234567, to_number=12345)
        self.assertIsNotNone(submission_id)

    def test_should_reject_if_questionnaire_does_not_exist(self):
        text = "2 +ID %s +Q1 akshay +Q2 50 +Q3 2 " % self.entity_instance.id
        message = ""
        try:
            smsplayer.submit(dbm=self.dbm, text=text, from_number=1234567, to_number=12345)
        except FormModelDoesNotExistsException as ex:
            message = ex.message
        self.assertEquals(message, "The questionnaire with code 2 does not exists")

    def test_should_reject_if_question_does_not_exist(self):
        text = "1 +ID %s +Q1 akshay +Non_existing_Question 50 +Q3 2" % self.entity_instance.id
        message = ""
        try:
            smsplayer.submit(dbm=self.dbm, text=text, from_number=12345, to_number=12345)
        except FieldDoesNotExistsException as ex:
            message = ex.message
        self.assertEquals(message, "The field with code Non_existing_Question does not exists")

    def test_should_reject_if_from_number_not_registered(self):
        text = "1 +ID %s +Q1 akshay +Q2 50 +Q3 2" % self.entity_instance.id
        with self.assertRaises(NumberNotRegisteredException):
            smsplayer.submit(self.dbm, text, 23456, 1234)

    def test_should_return_from_reporter(self):
        from_reporter = smsplayer.get_from_reporter(self.dbm,1234567)
        print from_reporter
        self.assertEquals("Test_reporter",from_reporter["first_name"])
#        self.assertTrue(False)
