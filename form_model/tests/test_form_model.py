# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.documents import FormModelDocument
from mangrove.datastore.entity import  define_type
from mangrove.form_model.field import  TextField, IntegerField, SelectField
from mangrove.datastore import datarecord
from mangrove.errors.MangroveException import QuestionCodeAlreadyExistsException, EntityQuestionAlreadyExistsException, DataObjectAlreadyExists
from mangrove.form_model.form_model import FormModel, RegistrationFormModel
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.validation import NumericConstraint, TextConstraint


class TestFormModel(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        self.entity_type = ["HealthFacility", "Clinic"]
        define_type(self.dbm, ["HealthFacility", "Clinic"])
        self.name_type = DataDictType(self.dbm, name='Name', slug='name', primitive_type='string')
        self.name_type.save()
        self.string_ddtype = DataDictType(self.dbm, name='Default String Datadict Type', slug='string_default',
                                          primitive_type='string')
        self.int_ddtype = DataDictType(self.dbm, name='Default Int Datadict Type', slug='int_default',
                                       primitive_type='integer')

        self.string_ddtype.save()
        self.int_ddtype.save()

        self.entity_instance = datarecord.register(self.dbm, entity_type="HealthFacility.Clinic",
                                                   data=[("Name", "Ruby", self.name_type)], location=["India", "Pune"],
                                                   source="sms")
        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=self.string_ddtype)
        question2 = TextField(name="question1_Name", question_code="Q1", label="What is your name",
                              defaultValue="some default value", language="eng", length=TextConstraint(5, 10),
                              ddtype=self.string_ddtype)
        question3 = IntegerField(name="Father's age", question_code="Q2", label="What is your Father's Age",
                                 range=NumericConstraint(min=15, max=120), ddtype=self.int_ddtype)
        question4 = SelectField(name="Color", question_code="Q3", label="What is your favourite color",
                                options=[("RED", 1), ("YELLOW", 2)], ddtype=self.string_ddtype)

        self.form_model = FormModel(self.dbm, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                    form_code="1", type='survey', fields=[
                    question1, question2, question3, question4])
        self.form_model__id = self.form_model.save()

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def test_create_form_model(self):
        self.assertTrue(self.form_model__id)

    def test_get_form_model(self):
        e = self.dbm.get(self.form_model__id, FormModel)
        self.assertTrue(e.id)
        self.assertTrue(e.type == "survey")

    def test_should_add_name_of_form_model(self):
        saved = self.dbm.get(self.form_model__id, FormModel)
        self.assertTrue(saved.name == "aids")

    def test_should_add_label(self):
        saved = self.dbm.get(self.form_model__id, FormModel)
        self.assertTrue(saved.label['eng'] == "Aids form_model")

    def test_should_add_short_ids(self):
        saved = self.dbm.get(self.form_model__id, FormModel)
        self.assertTrue(saved.form_code == "1")

    def test_should_add_entity_id(self):
        saved = self.dbm.get(self.form_model__id, FormModel)
        self.assertListEqual(saved.entity_type, self.entity_type)

    def test_should_add_fields(self):
        saved = self.dbm.get(self.form_model__id, FormModel)
        self.assertTrue(len(saved.fields) == 4)
        self.assertTrue(saved.fields[1].name == "question1_Name")
        self.assertTrue(saved.fields[2].name == "Father's age")

    def test_should_add_integer_field_with_constraints(self):
        integer_question = self.dbm.get(self.form_model__id, FormModel).form_fields[2]
        range_constraint = integer_question.range
        self.assertTrue(integer_question.name == "Father's age")
        self.assertTrue(range_constraint.get("min"), 15)
        self.assertTrue(range_constraint.get("max"), 120)

    def test_should_add_select1_field(self):
        select_question = self.dbm.get(self.form_model__id, FormModel).form_fields[3]
        option_constraint = select_question.options

        self.assertEquals(len(option_constraint), 2)
        self.assertEquals(option_constraint[0].get("val"), 1)

    def test_should_add_new_field(self):
        form_model = self.dbm.get(self.form_model__id, FormModel)
        question = TextField(name="added_question", question_code="Q4", label="How are you", ddtype=self.string_ddtype)
        form_model.add_field(question)
        form_model.save()

        added_question = self.dbm.get(self.form_model__id, FormModel).form_fields[4]
        self.assertEquals(added_question.question_code, "Q4")

    def test_should_delete_field(self):
        form_model = self.dbm.get(self.form_model__id, FormModel)
        form_model.delete_field(question_code="Q3")
        form_model.save()
        form_model = self.dbm.get(self.form_model__id, FormModel, force_reload=True)
        self.assertEquals(len(form_model.fields), 3)

    def test_should_add_english_as_default_langauge(self):
        activeLangauges = self.form_model.activeLanguages
        self.assertTrue("eng" in activeLangauges)

    def test_should_add_language_to_form_model(self):
        self.form_model.add_language(language="fra", label="French Aids form_model")
        activeLangauges = self.form_model.activeLanguages
        self.assertEquals(len(activeLangauges), 2)
        self.assertTrue("fra" in activeLangauges)
        self.assertEquals(self.form_model.label['fra'], u'French Aids form_model')

    def test_should_delete_all_fields_from_document(self):
        form_model = self.dbm.get(self.form_model__id, FormModel)
        form_model.delete_all_fields()
        self.assertEquals(len(form_model.form_fields), 0)

    def test_should_delete_all_fields_from_questions(self):
        form_model = self.dbm.get(self.form_model__id, FormModel)
        form_model.delete_all_fields()
        self.assertEquals(len(form_model.form_fields), 0)

    def test_should_raise_exception_if_entity_field_already_exist(self):
        with self.assertRaises(EntityQuestionAlreadyExistsException):
            form_model = self.dbm.get(self.form_model__id, FormModel)
            question = TextField(name="added_question", question_code="Q5", label="How are you",
                                 entity_question_flag=True, ddtype=self.string_ddtype)
            form_model.add_field(question)
            form_model.save()

    def test_should_raise_exception_if_question_code_is_not_unique(self):
        with self.assertRaises(QuestionCodeAlreadyExistsException):
            form_model = self.dbm.get(self.form_model__id, FormModel)
            question = TextField(name="added_question", question_code="q1", label="How are you",
                                 ddtype=self.string_ddtype)
            form_model.add_field(question)
            form_model.save()

    def test_should_set_form_code(self):
        form_model = self.dbm.get(self.form_model__id, FormModel)
        form_model.form_code = "xyz"
        self.assertEquals(form_model.form_code, "xyz")

    def test_should_persist_ddtype(self):
        form_model = self.dbm.get(self.form_model__id, FormModel)

        self.assertEqual(form_model.fields[0].ddtype.slug, self.string_ddtype.slug)
        self.assertEqual(form_model.fields[0].ddtype.id, self.string_ddtype.id)
        self.assertEqual(form_model.fields[0].ddtype.name, self.string_ddtype.name)

        self.assertEqual(form_model.fields[1].ddtype.slug, self.string_ddtype.slug)
        self.assertEqual(form_model.fields[1].ddtype.id, self.string_ddtype.id)
        self.assertEqual(form_model.fields[1].ddtype.name, self.string_ddtype.name)

        self.assertEqual(form_model.fields[2].ddtype.slug, self.int_ddtype.slug)
        self.assertEqual(form_model.fields[2].ddtype.id, self.int_ddtype.id)
        self.assertEqual(form_model.fields[2].ddtype.name, self.int_ddtype.name)

        self.assertEqual(form_model.fields[3].ddtype.slug, self.string_ddtype.slug)
        self.assertEqual(form_model.fields[3].ddtype.id, self.string_ddtype.id)
        self.assertEqual(form_model.fields[3].ddtype.name, self.string_ddtype.name)


    def test_should_set_entity_type(self):
        form_model = self.dbm.get(self.form_model__id, FormModel)
        form_model.entity_id = "xyz"
        self.assertEquals(form_model.entity_id, "xyz")

    def test_should_create_a_questionnaire_from_dictionary(self):
        fields = [
                    {
                    "name": "What are you reporting on?",
                    "defaultValue": "",
                    "label": {
                        "eng": "Entity being reported on"
                    },
                    "entity_question_flag": True,
                    "type": "text",
                    "ddtype": self.string_ddtype.to_json(),
                    "question_code": "eid",
                    "length": {"min": 1, "max": 10},
                    },
                    {
                        "range": {
                            "max": 10,
                            "min": 0
                        },
                        "label": {"eng": ""},
                        "type": "integer",
                        "ddtype": self.int_ddtype.to_json(),
                        "name": "What is your age?",
                        "question_code": "AGE"
                    },
                    {
                        "choices": [
                                    {
                                    "text": {"eng": "Pune"}
                                },
                                    {
                                        "text": {"eng": "Bangalore"}
                                    }
                        ],
                        "label": {"eng": ""},
                        "type": "select",
                        "ddtype": self.string_ddtype.to_json(),
                        "name": "Where do you live?",
                        "question_code": "PLC"
                    }]
        document = FormModelDocument()
        document.json_fields = fields
        document.entity_type = ["Reporter"]
        document.document_type = "FormModel"
        document.form_code = "F1"
        document.name = "New Project"
        document.type = "survey"
        document.type = "survey"
        entityQ = TextField(name="What are you reporting on?", question_code="eid",
                            label={"eng": "Entity being reported on"}, entity_question_flag=True,
                            length=TextConstraint(min=1, max=10), ddtype=self.string_ddtype)
        ageQ = IntegerField(name="What is your age?", question_code="AGE", label={"eng": ""},
                            range=NumericConstraint(min=0, max=10), ddtype=self.int_ddtype)
        placeQ = SelectField(name="Where do you live?", question_code="PLC", label={"eng": ""},
                             options=[{"text": {"eng": "Pune"}}, {"text": {"eng": "Bangalore"}}],
                             single_select_flag=False, ddtype=self.string_ddtype)
        questions = [entityQ, ageQ, placeQ]
        questionnaire = FormModel.new_from_db(self.dbm, document)
        self.maxDiff = None
        self.assertListEqual(questionnaire.entity_type, ["Reporter"])
        self.assertEqual(questionnaire.name, "New Project")
        self.assertEqual(questionnaire.type, "survey")
        for i in range(len(questions)):
            self.assertEqual(questionnaire.form_fields[i]._to_json(), questions[i]._to_json())

    def test_should_validate_for_valid_integer_value(self):
        answers = {"ID": "1", "Q2": "16"}
        self.assertTrue(self.form_model.is_valid(answers))

    def test_should_return_error_for_invalid_integer_value(self):
        answers = {"id": "1", "q2": "200"}
        self.assertFalse(self.form_model.is_valid(answers))
        self.assertEqual(len(self.form_model.errors), 1)

    def test_should_ignore_field_validation_if_the_answer_is_not_present(self):
        answers = {"id": "1", "q1": "Asif Momin", "q2": "20"}
        expected_result = {"entity_question": "1", "question1_Name": "Asif Momin", "Father's age": 20}
        valid = self.form_model.is_valid(answers)
        self.assertTrue(valid)
        self.assertEqual(self.form_model.cleaned_data, expected_result)

    def test_should_validate_for_valid_text_value(self):
        answers = {"ID": "1", "Q1": "Asif Momin"}
        self.assertTrue(self.form_model.is_valid(answers))

    def test_should_return_errors_for_invalid_text_and_integer(self):
        answers = {"id": "1", "q1": "Asif", "q2": "200", "q3": "a"}
        self.assertFalse(self.form_model.is_valid(answers))
        self.assertEqual(len(self.form_model.errors), 2)

    def test_should_strip_whitespaces(self):
        answers = {"q1": "   My Name", "q2": "  40 ", "q3": "a     "}
        expected_cleaned_data = {"question1_Name": "My Name", "Father's age": 40, "Color": ["RED"]}
        valid = self.form_model.is_valid(answers)
        self.assertTrue(valid)
        self.assertEqual(0, len(self.form_model.errors))
        self.assertEqual(self.form_model.cleaned_data, expected_cleaned_data)

    def test_should_ignore_fields_without_values(self):
        answers = {"q1": "My Name", "q2": "", "q3": "   "}
        expected_cleaned_data = {"question1_Name": "My Name"}
        valid = self.form_model.is_valid(answers)
        self.assertTrue(valid)
        self.assertEqual(0, len(self.form_model.errors))
        self.assertEqual(self.form_model.cleaned_data, expected_cleaned_data)

    def test_should_set_name(self):
        self.form_model.name = 'test_name'
        self.assertEquals(self.form_model.name, 'test_name')

    def test_should_set_entity_type_in_doc(self):
        self.form_model.entity_type = ["WaterPoint", "Dam"]
        self.assertEqual(self.form_model.entity_type, ["WaterPoint", "Dam"])

    def test_should_return_location_from_answers(self):
        fields = [{"name": "location", "defaultValue": "", "label": {"eng": "locatin of entity"},
                   "entity_question_flag": False, "type": "text", "ddtype": self.string_ddtype.to_json(),
                   "question_code": "L", }]
        registration_form = RegistrationFormModel(self.dbm, fields=fields)
        registration_form.answers = {"location": "India,MH"}
        self.assertEqual(registration_form.location, ['India', 'MH'])

    def test_should_return_location_as_None_if_answers_not_present(self):
        fields = [{"name": "location", "defaultValue": "", "label": {"eng": "locatin of entity"},
                   "entity_question_flag": False, "type": "text", "ddtype": self.string_ddtype.to_json(),
                   "question_code": "L", }]
        registration_form = RegistrationFormModel(self.dbm, fields=fields)
        self.assertEqual(registration_form.location, None)

    def test_should_not_return_blank_in_location(self):
        fields = [{"name": "location", "defaultValue": "", "label": {"eng": "locatin of entity"},
                   "entity_question_flag": False, "type": "text", "ddtype": self.string_ddtype.to_json(),
                   "question_code": "L", }]
        registration_form = RegistrationFormModel(self.dbm, fields=fields)
        registration_form.answers = {"location": "India,MH, "}

        self.assertEqual(registration_form.location, ['India', 'MH'])

    def test_should_raise_exception_if_form_code_already_exists_on_creation(self):
        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=self.string_ddtype)
        form_model = FormModel(self.dbm, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                    form_code="1", type='survey', fields=[question1])
        with self.assertRaises(DataObjectAlreadyExists):
            form_model.save()

    def test_should_raise_exception_if_form_code_already_exists_on_updation(self):
        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=self.string_ddtype)
        form_model2 = FormModel(self.dbm, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                    form_code="2", type='survey', fields=[question1])
        form_model2.save()
        with self.assertRaises(DataObjectAlreadyExists):
            form_model2.form_code = "1"

    def test_should_not_raise_exception_if_form_code_is_updated(self):
        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=self.string_ddtype)
        form_model2 = FormModel(self.dbm, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                    form_code="2", type='survey', fields=[question1])
        form_model2.save()
        form_model2.form_code = "2"
        form_model2.save()
