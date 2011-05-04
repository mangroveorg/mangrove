# vim= ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.form_model.field import TextField, IntegerField, SelectField, DateField
from mangrove.form_model import field

class TestQuestion(unittest.TestCase):
    def setup(self):
        pass

    def test_should_create_text_question_type_for_default_english_language(self):
        expected_json = {
            "defaultValue": "some default value",
            "label": {"eng": "What is your name"},
            "name": "question1_Name",
            "question_code": "Q1",
            "type": "text"
        }
        question = TextField(name="question1_Name", question_code="Q1", label="What is your name",
                                defaultValue="some default value", language="eng")

        actual_json = question._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_integer_question_type_for_default_english_language(self):
        expected_json = {
            "label": {"eng": "What is your age"},
            "name": "Age",
            "question_code": "Q2",
            "range": {},
            "type": "integer",
            }
        question = IntegerField(name="Age",  question_code="Q2", label="What is your age",
                                   language="eng")
        actual_json = question._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_integer_question_type_for_default_english_language_with_range(self):
        expected_json = {
            "label": {"eng": "What is your age"},
            "name": "Age",
            "question_code": "Q2",
            "range": {"min": 15,"max": 120},
            "type": "integer",
            }
        question = IntegerField(name="Age", question_code="Q2", label="What is your age",
                                   language="eng",range={"min": 15,"max": 120})
        actual_json = question._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_select_one_question_type_for_default_english_language(self):
        expected_json = {
            "label": {"eng": "What is your favorite color"},
            "name": "color",
            "options": [{"text": {"eng": "RED"},"val": 1},{"text": {"eng": "YELLOW"},"val": 2},{"text":{"eng":"green"}}],
            "question_code": "Q3",
            "type": "select1",
            }
        question = SelectField(name="color", question_code="Q3", label="What is your favorite color",
                                   language="eng",options=[("RED",1),("YELLOW",2),('green')])
        actual_json = question._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_multi_select_question_type_for_default_english_language(self):
        expected_json = {
            "label": {"eng": "What is your favorite color"},
            "name": "color",
            "options": [{"text": {"eng": "RED"},"val": 1},{"text": {"eng": "YELLOW"},"val": 2},{"text":{"eng":"green"}}],
            "question_code": "Q3",
            "type": "select",
            }
        question = SelectField(name="color", question_code="Q3", label="What is your favorite color",
                                   language="eng",options=[("RED",1),("YELLOW",2),('green')],single_select_flag=False)
        actual_json = question._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_date_question(self):
        expected_json = {
            "label": {"eng": "What is your Birth Date"},
            "name": "birthdate",
            "range": {"min": "15/1/2008","max": "15/1/2011"},
            "format":"dd/mm/yyyy",
            "question_code": "Q6",
            "type": "date",
            }
        question = DateField(name="birthdate", question_code="Q6", label="What is your Birth Date",format="dd/mm/yyyy",
                                   range={"min": "15/1/2008","max": "15/1/2011"},language="eng")
        actual_json = question._to_json()
        self.assertEqual(actual_json, expected_json)


    def test_should_add_label_for_french_language(self):
        expected_json = {
            "defaultValue": "some default value",
            "label": {"eng": "What is your name","fra":"french label"},
            "name": "question1_Name",
            "question_code": "Q1",
            "type": "text"
        }
        question = TextField(name="question1_Name", question_code="Q1", label="What is your name",
                                defaultValue="some default value" )
        question.add_or_edit_label(language="fra",label="french label")
        actual_json = question._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_edit_label_for_english_language(self):
        expected_json = {
            "defaultValue": "some default value",
            "label": {"eng": "english label","fra":"french label"},
            "name": "question1_Name",
            "question_code": "Q1",
            "type": "text"
        }
        question = TextField(name="question1_Name", question_code="Q1", label="What is your name",
                                defaultValue="some default value" )
        question.add_or_edit_label(language="fra",label="french label")
        question.add_or_edit_label(label="english label")
        actual_json = question._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_add_entity_question(self):
        expected_json = {
            "defaultValue": "",
            "label": {"eng": "What is your name"},
            "name": "question1_Name",
            "question_code": "Q1",
            "type": "text",
            "entity_question_flag": True
        }
        question = TextField(name="question1_Name", question_code="Q1", label="What is your name",entity_question_flag=True)
        actual_json = question._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_field_from_dictionary(self):
        question_json = {
            "defaultValue": "",
            "label": {"eng": "What is your name"},
            "name": "question1_Name",
            "question_code": "Q1",
            "type": "text",
            "entity_question_flag": True
        }
        created_question = field.create_question_from(question_json)
        self.assertIsInstance(created_question, TextField)

    def test_should_create_field_with_validations(self):
        question_json = {
            "defaultValue": "",
            "label": {"eng": "What is your age"},
            "name": "question1_age",
            "question_code": "Q1",
            "type": "integer",
            "range":{"min":0, "max": 100},
            "entity_question_flag": False
        }
        created_question = field.create_question_from(question_json)
        self.assertIsInstance(created_question, IntegerField)
        self.assertEqual(created_question._dict["range"],{"min":0, "max":100})

    def test_should_create_field_with_options(self):
        question_json = {
            "name":"q3",
            "question_code":"qc3",
            "type":"select",
            "options":[{ "value":"c1" },
                       { "value":"c2" } ],
            "entity_question_flag":False}
        created_question = field.create_question_from(question_json)
        self.assertIsInstance(created_question, SelectField)
        self.assertEqual(created_question.SINGLE_SELECT_FLAG, False)
        
    def test_should_create_field_with_single_select_options(self):
        question_json = {
            "name":"q3",
            "question_code":"qc3",
            "type":"select1",
            "options":[{ "text":{"eng":"hello", "fr":"bonjour"},"value":"c1" },
                       { "text":{"eng":"world"},"value":"c2" } ],
            "entity_question_flag":False}

        expected_option_list = [{ "text":{"eng":"hello", "fr":"bonjour"},"value":"c1" },
                       { "text":{"eng":"world"},"value":"c2" } ]
        created_question = field.create_question_from(question_json)
        self.assertIsInstance(created_question, SelectField)
        self.assertEqual(created_question.SINGLE_SELECT_FLAG, True)
        self.assertEqual(created_question.options, expected_option_list)

