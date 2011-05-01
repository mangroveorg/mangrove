# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import define_type
from mangrove.datastore.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import FormModel, FormSubmission

class TestFormSubmission(TestCase):
    def test_should_create_form_submission_with_entity_id(self):
        dbm = Mock(spec = DatabaseManager)
        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity"
                              , language="eng", entity_question_flag=True)
        question2 = TextField(name="question1_Name", question_code="Q1", label="What is your name",
                              defaultValue="some default value", language="eng")
        question3 = IntegerField(name="Father's age", question_code="Q2", label="What is your Father's Age",
                                 range={"min": 15, "max": 120})
        question4 = SelectField(name="Color", question_code="Q3", label="What is your favourite color",
                                options=[("RED", 1), ("YELLOW", 2)])

        form_model = FormModel(dbm, entity_type_id="Clinic", name="aids", label="Aids form_model",
                                    form_code="AIDS", type='survey',
                                    fields = [question1, question2, question3,question4])

        answers = { "ID" : "1", "Q1" : "My Name", "Q2" : "40", "Q3" : "RED"  }

        form_submission = FormSubmission(form_model,answers)
        self.assertEqual(form_submission.form_code,"AIDS")
        self.assertEqual(form_submission.entity_id,"1")


    def test_should_create_form_submission_with_answer_values(self):
        dbm = Mock(spec = DatabaseManager)
        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity"
                              , language="eng", entity_question_flag=True)
        question2 = TextField(name="Name", question_code="Q1", label="What is your name",
                              defaultValue="some default value", language="eng")
        question3 = IntegerField(name="Father's age", question_code="Q2", label="What is your Father's Age",
                                 range={"min": 15, "max": 120})
        question4 = SelectField(name="Color", question_code="Q3", label="What is your favourite color",
                                options=[("RED", 1), ("YELLOW", 2)])

        form_model = FormModel(dbm, entity_type_id="Clinic", name="aids", label="Aids form_model",
                                    form_code="AIDS", type='survey',
                                    fields = [question1, question2, question3,question4])

        answers = { "ID" : "1", "Q1" : "My Name", "Q2" : "40", "Q3" : "RED"  }
        form_submission = FormSubmission(form_model,answers)
        self.assertEqual(form_submission.values,{ "Name" : "My Name", "Father's age" : 40, "Color" : "RED"})

    def test_should_apply_validations(self):
        pass
#        Write negative scenarios
#        Write is_valid scenarios

        

