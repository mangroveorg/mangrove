import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.entity import define_type
from mangrove.datastore.field import SelectField, IntegerField, TextField
from mangrove.datastore.submission_api import submit
from mangrove.datastore import datarecord
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, EntityQuestionCodeNotSubmitted, FieldDoesNotExistsException, EntityInstanceDoesNotExistsException
from mangrove.form_model.form_model import FormModel

class TestSubmissionAPI(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        self.entity = define_type(self.dbm, ["HealthFacility", "Clinic"])
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

    def tearDown(self):
        del self.dbm.database[self.form_model__id]
        _delete_db_and_remove_db_manager(self.dbm)
        pass


    def test_should_submission(self):
        data_record_id = submit(self.dbm, self.form_model.form_code,
                                {"ID": self.entity_instance.id, "Q1": "Ans1", "Q2": "Ans2"}, "SMS")
        self.assertTrue(data_record_id)

    def test_should_raise_exception_if_form_model_does_not_exist(self):
        with self.assertRaises(FormModelDoesNotExistsException) as ex:
            submit(self.dbm, "test", {"Q1": "Ans1", "Q2": "Ans2"}, "SMS")

    def test_should_raise_exception_if_entity_question_code_not_submitted(self):
        with self.assertRaises(EntityQuestionCodeNotSubmitted):
            submit(self.dbm, self.form_model.form_code, {"Q1": "Ans1", "Q2": "Ans2"}, "SMS")

    def test_should_raise_exception_if_field_does_not_exist(self):
        with self.assertRaises(FieldDoesNotExistsException):
            submit(self.dbm, self.form_model.form_code, {"ID": self.entity_instance.id, "Q1": "Ans1", "Q5": "Ans2"},
                   "SMS")

    def test_should_raise_exception_if_entity_does_not_exist(self):
        message = ""
        try:
            submit(self.dbm,self.form_model.form_code,{"ID": "700", "Q1": "Ans1", "Q2": "Ans2"},"SMS")
        except EntityInstanceDoesNotExistsException as ex:
            message = ex.message
        self.assertEquals(message,"Entity with id 700 does not exist")
