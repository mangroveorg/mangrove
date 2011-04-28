# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.entity import  define_type
from mangrove.datastore.form_model import FormModel, get, submit, get_entity_field
from mangrove.datastore.field import field_attributes, TextField, IntegerField, SelectField
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, EntityQuestionCodeNotSubmitted, FieldDoesNotExistsException, EntityQuestionAlreadyExistsException, QuestionCodeAlreadyExistsException
import mangrove.datastore.datarecord as datarecord

class TestFormModel(unittest.TestCase):
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

    def test_create_form_model(self):
        self.assertTrue(self.form_model__id)

    def test_get_form_model(self):
        e = get(self.dbm, self.form_model__id)
        self.assertTrue(e.id)
        self.assertTrue(e.type == "survey")

    def test_should_add_name_of_form_model(self):
        saved = get(self.dbm, self.form_model__id)
        self.assertTrue(saved.name == "aids")

    def test_should_add_label(self):
        saved = get(self.dbm, self.form_model__id)
        self.assertTrue(saved.label['eng'] == "Aids form_model")

    def test_should_add_short_ids(self):
        saved = get(self.dbm, self.form_model__id)
        self.assertTrue(saved.form_code == "1")

    def test_should_add_entity_id(self):
        saved = get(self.dbm, self.form_model__id)
        self.assertTrue(saved.entity_id == self.entity.id)

    def test_should_add_fields(self):
        saved = get(self.dbm, self.form_model__id)
        self.assertTrue(len(saved.fields) == 4)
        self.assertTrue(saved.fields[1].get("name") == "question1_Name")
        self.assertTrue(saved.fields[2].get("name") == "Father's age")

    def test_should_add_integer_field_with_constraints(self):
        integer_question = get(self.dbm, self.form_model__id).fields[2]
        range_constraint = integer_question.get("range")
        self.assertTrue(integer_question.get("name") == "Father's age")
        self.assertTrue(range_constraint.get("min"), 15)
        self.assertTrue(range_constraint.get("max"), 120)

    def test_should_add_select1_field(self):
        select_question = get(self.dbm, self.form_model__id).fields[3]
        option_constraint = select_question.get("options")

        self.assertEquals(len(option_constraint), 2)
        self.assertEquals(option_constraint[0].get("val"), 1)

    def test_should_add_new_field(self):
        form_model = get(self.dbm, self.form_model__id)
        question = TextField(name="added_question", question_code="Q4", label="How are you")
        form_model.add_field(question)
        form_model.save()

        added_question = get(self.dbm, self.form_model__id).fields[4]
        self.assertEquals(added_question.get(field_attributes.FIELD_CODE), "Q4")

    def test_should_delete_field(self):
        form_model = get(self.dbm, self.form_model__id)
        form_model.delete_field(question_code="Q3")
        form_model.save()
        form_model = get(self.dbm, self.form_model__id)
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

    def test_should_get_entity_type_field(self):
        entity_question = get_entity_field(self.dbm, "1")
        self.assertEquals(entity_question.get(field_attributes.FIELD_CODE), "ID")
        self.assertEquals(entity_question.get(field_attributes.ENTITY_QUESTION_FLAG), True)

    def test_should_submission(self):
        data_record_id = submit(self.dbm, self.form_model.form_code,
                                {"ID": self.entity_instance.id, "Q1": "Ans1", "Q2": "Ans2"}, "SMS")
        self.assertTrue(data_record_id)

    def test_should_raise_exception_if_form_model_does_not_exist(self):
        with self.assertRaises(FormModelDoesNotExistsException) as ex:
            submit(self.dbm, "test", {"Q1": "Ans1", "Q2": "Ans2"}, "SMS")

    def test_should_delete_all_fields(self):
        form_model = get(self.dbm, self.form_model__id)
        form_model.delete_all_fields()
        form_model.save()
        form_model = get(self.dbm, self.form_model__id)
        self.assertEquals(len(form_model.fields), 0)

    def test_should_raise_exception_if_entity_field_code_not_submitted(self):
        with self.assertRaises(EntityQuestionCodeNotSubmitted):
            submit(self.dbm, self.form_model.form_code, {"Q1": "Ans1", "Q2": "Ans2"}, "SMS")

    def test_should_raise_exception_if_field_does_not_exist(self):
        with self.assertRaises(FieldDoesNotExistsException):
            submit(self.dbm, self.form_model.form_code, {"ID": self.entity_instance.id, "Q1": "Ans1", "Q5": "Ans2"},
                   "SMS")

    def test_should_raise_exception_if_entity_field_already_exist(self):
        with self.assertRaises(EntityQuestionAlreadyExistsException):
            form_model = get(self.dbm, self.form_model__id)
            question = TextField(name="added_question", question_code="Q5", label="How are you",entity_question_flag=True)
            form_model.add_field(question)
            form_model.save()

    def test_should_raise_exception_if_question_code_is_not_unique(self):
        with self.assertRaises(QuestionCodeAlreadyExistsException):
            form_model = get(self.dbm, self.form_model__id)
            question = TextField(name="added_question", question_code="Q1",label="How are you")
            form_model.add_field(question)
            form_model.save()

