import unittest
from mangrove.errors.MangroveException import GeoCodeFormatException
from mangrove.forms.fields import GeoCodeField
from mangrove.forms.validators import TextLengthValidator, RegexValidator
from mangrove.forms.fields import HierarchyField
from mangrove.forms.fields import TextField

class TestTextField(unittest.TestCase):
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
                          "instruction": "",
                          "required":False,
                          "validators": []
                          }, f.to_json())

    def test_should_validate_text(self):
        field = TextField(name="foo", code="bar", label="pipe", validators=[TextLengthValidator(1,2), RegexValidator("^[A-Za-z0-9]+$")])
        self.assertEqual((['the value "foo." is too long.',
                          'Invalid Mobile Number. Only Numbers and Dash(-) allowed.'], "foo."),
                                                                                     field.validate("foo."))
        self.assertEqual(([], "fo"), field.validate("fo"))


class TestHierarchyField(unittest.TestCase):
    def test_should_create_list_field_type_for_default_english_language(self):
        expected_json = {
            '_class': 'HierarchyField',
            "label": "What is your location",
            "name": "loc",
            "instruction": "Answer is list",
            "code": "Q1",
            "required":False,
            "validators": []
            }
        field = HierarchyField(name="loc", code="Q1", label="What is your location", instruction="Answer is list")
        self.assertEqual(expected_json, field.to_json())

    def test_should_validate_list_types(self):
        field = HierarchyField(name="loc", code="Q1", label="What is your location", instruction="Answer is list")
        value = ["a", "b", "c"]
        self.assertEqual(([], value), field.validate(value))
        self.assertEqual((["The value should be a sequence"], "eewewewe"), field.validate("eewewewe"))

class TestLocationField(unittest.TestCase):
    def test_should_create_location_field_type_for_default_english_language(self):
        expected_json = {
            "label": "Where do you stay?",
            "name": "field1_Loc",
            "code": "Q1",
            "_class": "GeoCodeField",
            "required":False,
            "instruction": "test_instruction",
            "validators": []
        }
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?", instruction="test_instruction", )
        self.assertEqual(expected_json, field.to_json())

    def test_should_validate_location(self):
        expect_lat_long = ([], (89.1, 100.1))
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?")
        actual_lat_long = field.validate("89.1 100.1")
        self.assertEqual(expect_lat_long, actual_lat_long)

    def test_should_validate_location_with_whitespaces(self):
        expect_lat_long = ([], (89.1, 100.1))
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?")
        actual_lat_long = field.validate(" 89.1    100.1  ")
        self.assertEqual(expect_lat_long, actual_lat_long)

    def test_should_give_error_for_invalid_location(self):
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?")
        exception = GeoCodeFormatException('89.1')
        self.assertEqual(([exception.message], '89.1'),field.validate("89.1"))
        self.assertEqual(([exception.message], ""),field.validate("   "))
        self.assertEqual(([exception.message], ""),field.validate(""))
        self.assertEqual(([exception.message], ""),field.validate(None))

