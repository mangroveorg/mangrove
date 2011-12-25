import unittest
from mangrove.forms.fields import TextField

class TestTestField(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_text_field(self):
        f = TextField("name", "na", "What is the name?")
        self.assertEqual("na", f.code)

    def test_text_field_to_json(self):
        f = TextField("name", "na", "What is the name?")
        self.assertEqual({'_class': 'TextField',
                          'name':"name",
                          'code':"na",
                          "label":"What is the name?",
                          "default": "",
                          "required":False,
                          "validators": []
                          }, f.to_json())



