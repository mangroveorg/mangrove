# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import FormModel, FormSubmission
from mangrove.form_model.validation import IntegerConstraint

class TestFormSubmission(TestCase):
    def setUp(self):
        self.datadict_patcher = patch("mangrove.form_model.form_model.datadict")
        self.datadict_module = self.datadict_patcher.start()
        self.dbm = Mock(spec = DatabaseManager)


    def tearDown(self):
        self.datadict_patcher.stop()


    def test_should_create_form_submission_with_entity_id(self):
        dbm = Mock(spec = DatabaseManager)
        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity"
                              , language="eng", entity_question_flag=True)
        question2 = TextField(name="question1_Name", question_code="Q1", label="What is your name",
                              defaultValue="some default value", language="eng")
        question3 = IntegerField(name="Father's age", question_code="Q2", label="What is your Father's Age",
                               range=IntegerConstraint(min=15,max=120))
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
        ddtype = DataDictType(self.dbm, name='Default Datadict Type', slug='default', primitive_type='string')
        self.datadict_module.get_default_datadict_type.return_value = ddtype

        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity"
                              , language="eng", entity_question_flag=True)
        question2 = TextField(name="Name", question_code="Q1", label="What is your name",
                              defaultValue="some default value", language="eng")
        question3 = IntegerField(name="Father's age", question_code="Q2", label="What is your Father's Age",
                                 range=IntegerConstraint(min=15,max=120))
        question4 = SelectField(name="Color", question_code="Q3", label="What is your favourite color",
                                options=[("RED", 1), ("YELLOW", 2)])

        form_model = FormModel(dbm, entity_type_id="Clinic", name="aids", label="Aids form_model",
                                    form_code="AIDS", type='survey',
                                    fields = [question1, question2, question3,question4])

        answers = { "ID" : "1", "Q1" : "My Name", "Q2" : "40", "Q3" : "RED"  }
        form_submission = FormSubmission(form_model,answers)
        self.assertEqual(form_submission.answers,{ "Name" : "My Name", "Father's age" : 40, "Color" : "RED"})
        self.assertEqual(3,len(form_submission.values))
        self.assertIn(("Name","My Name",ddtype),form_submission.values)
        self.assertIn(("Father's age",40,ddtype),form_submission.values)
        self.assertIn(("Color","RED",ddtype),form_submission.values)

    def test_should_ignore_non_form_fields(self):
        ddtype = DataDictType(self.dbm, name='Default Datadict Type', slug='default', primitive_type='string')
        self.datadict_module.get_default_datadict_type.return_value = ddtype

        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity"
                              , language="eng", entity_question_flag=True)
        question2 = TextField(name="Name", question_code="NAME", label="Clinic Name",
                          defaultValue="some default value", language="eng")
        question3 = IntegerField(name="Arv Stock", question_code="ARV", label="ARV Stock",
                             range=IntegerConstraint(min=15,max=120))

        form_model = FormModel(self.dbm, entity_type_id="Clinic", name="aids", label="Aids form_model",
                                form_code="CLINIC", type='survey',
                                fields=[question1, question2, question3])

        answers = { "ID" : "1", "NAME" : "My name", "ARV" : "10", "EXTRA_FIELD" : "X", "EXTRA_FIELD2" : "Y"}

        f = FormSubmission(form_model,answers)

        self.assertEqual({"Name" : "My name", "Arv Stock" : 10},f.answers)
        self.assertEqual(2,len(f.values))
        self.assertIn(("Name","My name",ddtype),f.values)
        self.assertIn(("Arv Stock",10,ddtype),f.values)

    def test_should_apply_validations(self):
        pass
#        Write negative scenarios
#        Write is_valid scenarios

        

