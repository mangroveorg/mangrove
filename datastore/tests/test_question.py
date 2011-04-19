# vim= ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.question import IntegerQuestion, TextQuestion, QuestionBuilder

class TestQuestion(unittest.TestCase):
    def setup(self):
        pass

    def test_should_create_text_question_type_for_default_english_language(self):
        expected_json = {
            "defaultValue": "some default value",
            "label": [{"eng": "What is your name"}],
            "name": "question1_Name",
            "sms_code": "Q1",
            "type": "text"
        }
        question = QuestionBuilder(type="text", name="question1_Name", sms_code="Q1", label="What is your name",
                                defaultValue="some default value", language="eng")
        actual_json = question.to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_integer_question_type_for_default_english_language(self):
        expected_json = {
            "label": [{"eng": "What is your age"}],
            "name": "Age",
            "sms_code": "Q2",
            "range": {},
            "type": "integer",
            }
        question = QuestionBuilder(type="integer",name="Age",  sms_code="Q2", label="What is your age",
                                   language="eng")
        actual_json = question.to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_integer_question_type_for_default_english_language_with_range(self):
        expected_json = {
            "label": [{"eng": "What is your age"}],
            "name": "Age",
            "sms_code": "Q2",
            "range": {"min": 15,"max": 120},
            "type": "integer",
            }
        question = QuestionBuilder(name="Age", type="integer", sms_code="Q2", label="What is your age",
                                   language="eng",range={"min": 15,"max": 120})
        actual_json = question.to_json()
        self.assertEqual(actual_json, expected_json)


    