import unittest
from mangrove.forms.fields import Field, TelephoneNumberField, HierarchyField, TextField, GeoCodeField
from mangrove.errors.MangroveException import GeoCodeFormatException, RegexMismatchException
from mangrove.forms.validators import TextLengthValidator, RegexValidator

class TestTextField(unittest.TestCase):
    def test_create_text_field(self):
        f = TextField("na", "What is the name?")
        self.assertEqual("na", f.code)

    def test_text_field_to_json(self):
        f = TextField("na", "What is the name?")
        self.assertEqual({'_class': 'TextField',
                          'code':"na",
                          "label":"What is the name?",
                          "default": "",
                          "instruction": "",
                          "required":False,
                          "validators": []
                          }, f.to_json())

    def test_should_validate_text(self):
        field = TextField(code="bar", label="pipe", validators=[TextLengthValidator(1,2), RegexValidator("^[A-Za-z0-9]+$")], required=True)
        self.assertEqual((['the value "foo." is too long.',
                          'Invalid Mobile Number. Only Numbers and Dash(-) allowed.'], "foo."),
                                                                                     field.validate("foo."))
        self.assertEqual(([], "fo"), field.validate("fo"))
        self.assertEqual((['This field is required.'], ''), field.validate(""))



class TestHierarchyField(unittest.TestCase):
    def test_should_create_list_field_type_for_default_english_language(self):
        expected_json = {
            '_class': 'HierarchyField',
            "label": "What is your location",
            "instruction": "Answer is list",
            "code": "Q1",
            "required":False,
            "validators": []
            }
        field = HierarchyField(code="Q1", label="What is your location", instruction="Answer is list")
        self.assertEqual(expected_json, field.to_json())

    def test_should_validate_list_types(self):
        field = HierarchyField(code="Q1", label="What is your location", instruction="Answer is list")
        value = ["a", "b", "c"]
        self.assertEqual(([], value), field.validate(value))
        self.assertEqual((["The value should be a sequence"], "eewewewe"), field.validate("eewewewe"))

class TestLocationField(unittest.TestCase):
    def test_should_create_location_field_type_for_default_english_language(self):
        expected_json = {
            "label": "Where do you stay?",
            "code": "Q1",
            "_class": "GeoCodeField",
            "required":False,
            "instruction": "test_instruction",
            "validators": []
        }
        field = GeoCodeField(code="Q1", label="Where do you stay?", instruction="test_instruction", )
        self.assertEqual(expected_json, field.to_json())

    def test_should_validate_location(self):
        expect_lat_long = ([], (89.1, 100.1))
        field = GeoCodeField(code="Q1", label="Where do you stay?")
        actual_lat_long = field.validate("89.1 100.1")
        self.assertEqual(expect_lat_long, actual_lat_long)

    def test_should_validate_location_with_whitespaces(self):
        expect_lat_long = ([], (89.1, 100.1))
        field = GeoCodeField(code="Q1", label="Where do you stay?")
        actual_lat_long = field.validate(" 89.1    100.1  ")
        self.assertEqual(expect_lat_long, actual_lat_long)

    def test_should_give_error_for_invalid_location(self):
        field = GeoCodeField(code="Q1", label="Where do you stay?")
        exception = GeoCodeFormatException('89.1')
        self.assertEqual(([exception.message], '89.1'),field.validate("89.1"))
        self.assertEqual(([exception.message], ""),field.validate("   "))
        self.assertEqual(([exception.message], ""),field.validate(""))
        self.assertEqual(([exception.message], ""),field.validate(None))

class TestTelephoneNumberField(unittest.TestCase):

    def test_telephone_number_field_should_return_expected_json(self):
        mobile_number_length = TextLengthValidator(max=15)
        mobile_number_pattern = RegexValidator('^[0-9]+$')
        field = TelephoneNumberField(code='MC', label='question',
                                     validators=[mobile_number_length, mobile_number_pattern])
        expected_json = {
            "label": "question",
            "code": "MC",
            "instruction": "",
            "validators": [
                    {
                    '_class': 'TextLengthValidator',
                    'max': 15},
                    {
                    '_class': 'RegexValidator',
                    'pattern': '^[0-9]+$'}],
            "required": False,
            "_class": "TelephoneNumberField"
        }
        self.assertEqual(expected_json, field.to_json())

    def test_should_create_telephone_number_field_from_dictionary(self):
        field_json = {
            "label": "test",
            "code": "Q1",
            "validators": [{'_class': 'TextLengthValidator', "min": 1, "max": 10}, {
                '_class': 'RegexValidator',
                'pattern': '^[0-9]+$'}],
            "instruction": "some instruction",
            "required": False,
            "_class": "TelephoneNumberField"
        }
        field = Field.build_from_dct(field_json)

        self.assertIsInstance(field, TelephoneNumberField)
        self.assertIsInstance(field.validators[0], TextLengthValidator)
        self.assertIsInstance(field.validators[1], RegexValidator)
        self.assertEqual(field.validators[0].max, 10)
        self.assertEqual(field.validators[0].min, 1)
        self.assertEqual(field.label, "test")
        self.assertEqual(field.instruction, "some instruction")
        self.assertFalse(field.required)

    def test_telephone_number_should_clean_value_to_remove_only_hyphen_from_the_given_value(self):
        pattern = '^[0-9]+$'
        field = TelephoneNumberField(code='MC', label='question',
                                     validators=[(TextLengthValidator(max=15)), (RegexValidator(pattern))])

        self.assertEqual(([], '1234321122'), field.validate('123-4321122'))
        self.assertEqual(([RegexMismatchException(pattern).message], '123dsasa4321122'), field.validate('123dsasa4321122'))

    def test_should_convert_text_in_epsilon_format_to_expanded_text(self):
        field = TelephoneNumberField(code='MC', label='question',
                                     validators=[(TextLengthValidator(max=15)), (RegexValidator('^[0-9]+$'))])
        self.assertEqual(([], u'266123321435'), field.validate(u'2.66123321435e+11'))

    def test_should_raise_regex_mismatch_exception_if_invalid_phone_number(self):
        pattern = '^[0-9]+$'
        field = TelephoneNumberField(code='MC', label='question',
                                     validators=[(TextLengthValidator(max=15)), (RegexValidator(pattern))],)
        self.assertEqual(([RegexMismatchException(pattern).message], u'020321dsa'), field.validate(u'020321dsa'))