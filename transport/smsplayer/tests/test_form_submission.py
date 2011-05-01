# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.field import SelectField, IntegerField, TextField
from mangrove.form_model.form_model import FormModel, FormSubmission

class TestFormSubmission(TestCase):
    def test_should_ignore_non_form_fields(self):
        dbm = Mock(spec = DatabaseManager)
        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity"
                              , language="eng", entity_question_flag=True)
        question2 = TextField(name="Name", question_code="NAME", label="Clinic Name",
                          defaultValue="some default value", language="eng")
        question3 = IntegerField(name="Arv Stock", question_code="ARV", label="ARV Stock",
                             range={"min": 15, "max": 120})

        form_model = FormModel(dbm, entity_type_id="Clinic", name="aids", label="Aids form_model",
                                form_code="CLINIC", type='survey',
                                fields=[question1, question2, question3])

        answers = { "ID" : "1", "NAME" : "My name", "ARV" : "10", "EXTRA_FIELD" : "X", "EXTRA_FIELD2" : "Y"}

        f = FormSubmission(form_model,answers)

        self.assertEqual({"Name" : "My name", "Arv Stock" : 10},f.values)

