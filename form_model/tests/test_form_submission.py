# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import FormModel, FormSubmission
from mangrove.form_model.validation import NumericConstraint


class TestFormSubmission(TestCase):
    def setUp(self):

        self.dbm = Mock(spec=DatabaseManager)
        self.ddtype1 = Mock(spec=DataDictType)
        self.ddtype2 = Mock(spec=DataDictType)
        self.ddtype3 = Mock(spec=DataDictType)
        self.ddtype4 = Mock(spec=DataDictType)

        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=self.ddtype1)
        question2 = TextField(name="Name", code="Q1", label="What is your name",
                              defaultValue="some default value", language="eng", ddtype=self.ddtype2)
        question3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age",
                                 range=NumericConstraint(min=15, max=120), ddtype=self.ddtype3)
        question4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
                                options=[("RED", 1), ("YELLOW", 2)], ddtype=self.ddtype4)

        self.form_model = FormModel(self.dbm, entity_type=["Clinic"], name="aids", label="Aids form_model",
                                    form_code="AIDS", type='survey',
                                    fields=[question1, question2, question3, question4])

    def tearDown(self):
        pass

    def test_should_create_form_submission_with_entity_id(self):
        answers = {"id": "1", "q1": "My Name", "q2": "40", "q3": "RED"}

        form_submission = FormSubmission(self.form_model, answers,short_code='1', success=True,errors={},entity_type=["Clinic"],data={})

        self.assertEqual(form_submission.form_code, "aids")
        self.assertEqual(form_submission.short_code, "1")

    
    