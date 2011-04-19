# vim= ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.question import Question

class TestQuestion(unittest.TestCase):
    def setup(self):
        pass

    def test_should_create_text_question_type_for_default_english_language(self):
        expected_json = {
            "defaultValue": "some default value",
            "label": [{"eng":"What is your name"}],
            "name": "question1_Name",
            "sms_code": "Q1",
            "type": "text"
        }
        question = Question(name="question1_Name", type="text", sms_code="Q1", label="What is your name",
                            defaultValue="some default value",language="eng")
        actual_json = question.to_json()
        self.assertEqual(actual_json,expected_json)




    