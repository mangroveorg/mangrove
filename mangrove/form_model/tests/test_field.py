# vim= ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from datetime import datetime

from mock import Mock

from mangrove.datastore.database import DatabaseManager
from mangrove.errors.MangroveException import IncorrectDate, GeoCodeFormatException, RegexMismatchException, RequiredFieldNotPresentException
from mangrove.form_model.field import DateField, GeoCodeField, field_to_json, HierarchyField, TelephoneNumberField, Field, ShortCodeField, FieldSet
from mangrove.errors.MangroveException import AnswerTooBigException, AnswerTooSmallException, \
    AnswerTooLongException, AnswerTooShortException, AnswerWrongType, AnswerHasTooManyValuesException
from mangrove.form_model.field import TextField, IntegerField, SelectField, ExcelDate, UniqueIdField
from mangrove.form_model import field
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint, RegexConstraint


class TestField(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)

    def test_should_create_text_field_type_for_default_english_language(self):
        expected_json = {
            "defaultValue": "some default value",
            "label": "What is your name",
            "name": "field1_Name",
            "instruction": "Answer is word or phrase",
            "code": "Q1",
            "parent_field_code": None,
            "constraints": [("length", {"min": 1, "max": 20})],
            "type": "text",
            "required": True,
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        field = TextField(name="field1_Name", code="Q1", label="What is your name",
                          defaultValue="some default value", constraints=[TextLengthConstraint(1, 20)], instruction="Answer is word or phrase")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

        field.set_value("abc")
        self.assertEqual("abc", field.convert_to_unicode())

    def test_should_create_list_field_type_for_default_english_language(self):
        expected_json = {
            "label": "What is your location",
            "name": "loc",
            "instruction": "Answer is list",
            "parent_field_code": None,
            "code": "Q1",
            "type": "list",
            "required": True,
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        field = HierarchyField(name="loc", code="Q1", label="What is your location", instruction="Answer is list")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

        field.set_value(["abc", "def"])
        self.assertEqual("abc,def", field.convert_to_unicode())


    def test_should_create_integer_field_type_for_default_english_language(self):
        expected_json = {
            "label": "What is your age",
            "name": "Age",
            "code": "Q2",
            "type": "integer",
            'parent_field_code': None,
            "required": True,
            "instruction": "test_instruction",
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        field = IntegerField(name="Age", code="Q2", label="What is your age",
                             instruction="test_instruction")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)
        field.set_value(123)
        self.assertEqual("123", field.convert_to_unicode())

    def test_should_set_new_name_for_field(self):
        new_name = "newName"
        instruction = "test_instruction"
        expected_json = {
            "label": "What is your age",
            "name": new_name,
            "code": "Q2",
            "parent_field_code": None,
            "type": "integer",
            "required": True,
            "instruction": instruction,
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        field = Field(type="integer", name="oldName", code="Q2", label="What is your age",
                      instruction=instruction)
        field.set_name(new_name)
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_set_new_instruction_for_field(self):
        new_instruction = "new_instruction"
        expected_json = {
            "label": "What is your age",
            "name": "name",
            "code": "Q2",
            "parent_field_code": None,
            "type": "integer",
            "required": True,
            "instruction": new_instruction,
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        field = Field(type="integer", name="name", code="Q2", label="What is your age",
                      instruction="instruction")
        field.set_instruction(new_instruction)
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_integer_field_type_with_range(self):
        expected_json = {
            "label": "What is your age",
            "name": "Age",
            "code": "Q2",
            "constraints": [('range', {"min": 15, "max": 120})],
            "parent_field_code": None,
            "type": "integer",
            "required": True,
            "instruction": "test_instruction",
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        field = IntegerField(name="Age", code="Q2", label="What is your age",
                             constraints=[NumericRangeConstraint(min=15, max=120)],
                             instruction="test_instruction")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_select_one_field_type_for_default_english_language(self):
        expected_json = {
            "label": "What is your favorite color",
            "name": "color",
            "choices": [{"text": "RED", "val": 'a'}, {"text": "YELLOW", "val": 'b'},
                        {"text": 'green', "val": 'c'}],
            "code": "Q3",
            "parent_field_code": None,
            "type": "select1",
            "required": True,
            "instruction": None,
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        field = SelectField(name="color", code="Q3", label="What is your favorite color",
                            options=[("RED", 'a'), ("YELLOW", 'b'), ('green', 'c')])
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

        field.set_value(field.validate('b'))
        self.assertEqual("YELLOW", field.convert_to_unicode())

    def test_should_create_multi_select_field_type_for_default_english_language(self):
        expected_json = {
            "label": "What is your favorite color",
            "name": "color",
            "choices": [{"text": "RED", "val": 'a'}, {"text": "YELLOW", "val": 'b'},
                        {"text": 'green', 'val':'green'}],
            "code": "Q3",
            "parent_field_code": None,
            "type": "select",
            "required": True,
            "instruction": "test_instruction",
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        field = SelectField(name="color", code="Q3", label="What is your favorite color",
                            options=[("RED", 'a'), ("YELLOW", 'b'), ('green')], single_select_flag=False,
                             instruction="test_instruction")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)
        field.set_value(field.validate('ab'))
        self.assertEqual("RED,YELLOW", field.convert_to_unicode())

    def test_should_remove_spaces_if_present_in_answer_for_multi_select(self):
        field = SelectField(name="color", code="Q3", label="What is your favorite color",
                            options=[("RED", 'a'), ("YELLOW", 'b'), ('green')], single_select_flag=False,
                             instruction="test_instruction")
        self.assertEqual(['RED', 'YELLOW'], field.validate('a b'))

    def test_should_add_entity_field_with_default_constraints(self):
        expected_json = {
            "defaultValue": "",
            "label": "What is your name",
            "name": "field1_Name",
            "code": "Q1",
            "type": "short_code",
            'parent_field_code': None,
            "constraints": [("length", {"max": 20}), ("short_code", "^[a-zA-Z0-9]+$")],
            "required": False,
            "instruction": "test_instruction",
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        field = ShortCodeField(name="field1_Name", code="Q1", label="What is your name",
                          instruction="test_instruction")
        actual_json = field._to_json()
        self.assertDictEqual(actual_json, expected_json)

    def test_should_create_text_field_from_dictionary(self):
        field_json = {
            "defaultValue": "",
            "label": "What is your name",
            "name": "field1_Name",
            "code": "Q1",
            "type": "text",
            "constraints": [("length", {"min": 1, "max": 10})],
            "entity_field_flag": True,
            "required": False,
            "instruction": "some instruction"
        }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, TextField)
        self.assertIsInstance(created_field.constraints[0], TextLengthConstraint)
        self.assertEqual(created_field.constraints[0].max, 10)
        self.assertEqual(created_field.constraints[0].min, 1)
        self.assertEqual(created_field.label, "What is your name")
        self.assertEqual(created_field.instruction, "some instruction")
        self.assertFalse(created_field.is_required())

    def test_should_create_text_field_from_dictionary_with_multiple_labels(self):
        field_json = {
            "defaultValue": "",
            "label": "What is your name",
            "name": "field1_Name",
            "code": "Q1",
            "type": "text",
            "constraints": [("length", {"min": 1, "max": 10})],
            "entity_field_flag": True,
            "required": False,
            "instruction": "some instruction"
        }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, TextField)
        self.assertIsInstance(created_field.constraints[0], TextLengthConstraint)
        self.assertEqual(created_field.constraints[0].max, 10)
        self.assertEqual(created_field.constraints[0].min, 1)
        self.assertEqual(created_field.label, "What is your name")
        self.assertEqual(created_field.instruction, "some instruction")
        self.assertFalse(created_field.is_required())

    def test_should_create_integer_field_with_validations(self):
        field_json = {
            "defaultValue": "",
            "label": "What is your age",
            "name": "field1_age",
            "code": "Q1",
            "type": "integer",
            
            'constraints': [("range", {"min": 0, "max": 100})],
            "required": True,
            "entity_field_flag": False
        }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, IntegerField)
        self.assertEqual(created_field._dict["constraints"][0][1], {"min": 0, "max": 100})
        self.assertIsInstance(created_field.constraints[0], NumericRangeConstraint)
        self.assertEqual(created_field.constraints[0].max, 100)
        self.assertEqual(created_field.constraints[0].min, 0)
        self.assertTrue(created_field.is_required())

    def test_should_create_integer_field_with_multiple_labels(self):
        LABEL = "What is your age"
        field_json = {
            "defaultValue": "",
            "label": LABEL,
            "name": "field1_age",
            "code": "Q1",
            "type": "integer",
            
            'constraints': [("range", {"min": 0, "max": 100})],
            "required": True,
            "entity_field_flag": False
        }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, IntegerField)
        self.assertEqual(created_field._dict["constraints"][0][1], {"min": 0, "max": 100})
        self.assertIsInstance(created_field.constraints[0], NumericRangeConstraint)
        self.assertEqual(LABEL, created_field.label)
        self.assertEqual(created_field.constraints[0].max, 100)
        self.assertEqual(created_field.constraints[0].min, 0)
        self.assertTrue(created_field.is_required())

    def test_should_create_select_field_with_options(self):
        field_json = {
            "name": "q3",
            "code": "qc3",
            "type": "select",
            
            "choices": [{"text": "option 1", "value": "c1"},
                        {"text": "option 1", "value": "c2"}],
            "required": False,
            "entity_field_flag": False,
            "label": "select type field"}
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, SelectField)
        self.assertEqual(created_field.single_select_flag, False)
        self.assertFalse(created_field.is_required())

    def test_should_create_select_field_with_multiple_labels(self):
        LABEL = "select type field"
        field_json = {
            "name": "q3",
            "code": "qc3",
            "type": "select",
            
            "choices": [{"text": "option 1", "value": "c1"},
                        {"text": "option 1", "value": "c2"}],
            "required": False,
            "entity_field_flag": False,
            "label": LABEL}
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, SelectField)
        self.assertEqual(LABEL, created_field.label)
        self.assertEqual(created_field.single_select_flag, False)
        self.assertFalse(created_field.is_required())

    def test_should_create_hierarchy_field_with_multiple_labels(self):
        LABEL = "hierarchy type field"
        field_json = {
            "name": "q3",
            "code": "qc3",
            "type": "list",
            
            "required": False,
            "entity_field_flag": False,
            "label": LABEL}
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, HierarchyField)
        self.assertEqual(LABEL, created_field.label)
        self.assertFalse(created_field.is_required())

    def test_should_create_telephone_number_field_with_multiple_labels(self):
        LABEL = "telephone number field"
        field_json = {
            "name": "q3",
            "code": "qc3",
            "type": "telephone_number",
            
            "required": False,
            "label": LABEL}
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, TelephoneNumberField)
        self.assertEqual(LABEL, created_field.label)
        self.assertFalse(created_field.is_required())

    def test_should_create_select_field_with_single_select_options(self):
        field_json = {
            "name": "q3",
            "code": "qc3",
            "type": "select1",
            
            "choices": [{"text": "hello", "value": "c1"},
                        {"text": "world", "value": "c2"}],
            "required": False,
            "entity_field_flag": False,
            "label": "select1 type question"}

        expected_option_list = [{"text": "hello", "value": "c1"},
                                {"text": "world", "value": "c2"}]
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, SelectField)
        self.assertEqual(created_field.single_select_flag, True)
        self.assertEqual(created_field.options, expected_option_list)
        self.assertFalse(created_field.is_required())

    def test_should_return_error_for_integer_range_validation(self):
        field = IntegerField(name="Age", code="Q2", label="What is your age",
                             constraints=[NumericRangeConstraint(min=15, max=120)])
        valid_value = field.validate("120")
        self.assertEqual(valid_value, 120)
        valid_value = field.validate("25.5")
        self.assertEqual(valid_value, 25.5)

    def test_should_return_error_for_wrong_type_for_integer(self):
        with self.assertRaises(AnswerWrongType) as e:
            field = IntegerField(name="Age", code="Q2", label="What is your age",
                                 constraints=[NumericRangeConstraint(min=15, max=120)])
            field.validate("asas")
        self.assertEqual(e.exception.message, "Answer asas for question Q2 is of the wrong type.")

    def test_should_return_error_for_integer_range_validation_for_max_value(self):
        with self.assertRaises(AnswerTooBigException) as e:
            field = IntegerField(name="Age", code="Q2", label="What is your age",
                                 constraints=[NumericRangeConstraint(min=15, max=120)])
            valid_value = field.validate(150)
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message, "Answer 150 for question Q2 is greater than allowed.")

    def test_should_return_error_for_integer_range_validation_for_min_value(self):
        with self.assertRaises(AnswerTooSmallException) as e:
            field = IntegerField(name="Age", code="Q2", label="What is your age",
                                 constraints=[NumericRangeConstraint(min=15, max=120)])
            valid_value = field.validate(11)
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message, "Answer 11 for question Q2 is smaller than allowed.")

    def test_successful_text_length_validation(self):
        field = TextField(name="Name", code="Q2", label="What is your Name",
                          constraints=[TextLengthConstraint(min=4, max=15)])
        field1 = TextField(name="Name", code="Q2", label="What is your Name")
        valid_value = field.validate("valid")
        self.assertEqual(valid_value, "valid")
        valid_value = field1.validate("valid")
        self.assertEqual(valid_value, "valid")

    def test_should_return_error_for_text_length_validation_for_max_value(self):
        with self.assertRaises(AnswerTooLongException) as e:
            field = TextField(name="Age", code="Q2", label="What is your age",
                              constraints=[TextLengthConstraint(min=1, max=4)])
            valid_value = field.validate("long_answer")
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message, "Answer long_answer for question Q2 is longer than allowed.")

    def test_should_return_error_for_text_length_validation_for_min_value(self):
        with self.assertRaises(AnswerTooShortException) as e:
            field = TextField(name="Age", code="Q2", label="What is your age",
                              constraints=[TextLengthConstraint(min=15, max=120)])
            valid_value = field.validate("short")
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message, "Answer short for question Q2 is shorter than allowed.")

    def test_should_create_date_field(self):
        field_json = {
            "defaultValue": "",
            "label": "What is your birth date",
            "name": "Birth_date",
            "code": "Q1",
            "type": "date",
            "date_format": "%m.%Y",
            
            "required": False
        }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, DateField)
        self.assertEqual(created_field.date_format, "%m.%Y")
        self.assertFalse(created_field.is_required())

    def test_should_create_date_field_with_multiple_labels(self):
        LABEL = "What is your birth date"
        field_json = {
            "defaultValue": "",
            "label": LABEL,
            "name": "Birth_date",
            "code": "Q1",
            "type": "date",
            "date_format": "%m.%Y",
            
            "required": False
        }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, DateField)
        self.assertEqual(created_field.date_format, "%m.%Y")
        self.assertEqual(LABEL, created_field.label)
        self.assertFalse(created_field.is_required())

    def test_should_create_geo_code_field(self):
        field_json = {
            "label": "What is your location",
            "name": "Birth_place",
            "code": "LOC",
            "type": "geocode",
            
            "required": True,
        }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, GeoCodeField)
        self.assertTrue(created_field.is_required())

    def test_should_create_geo_code_field_with_multiple_labels(self):
        LABEL = "What is your location"
        field_json = {
            "label": LABEL,
            "name": "Birth_place",
            "code": "LOC",
            "type": "geocode",
            
            "required": True,
        }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, GeoCodeField)
        self.assertEqual(LABEL, created_field.label)
        self.assertTrue(created_field.is_required())

    def test_should_return_error_for_incorrect_date_format_error_for_wrong_format(self):
        with self.assertRaises(IncorrectDate) as e:
            field = DateField(name="Age", code="Q2", label="What is your birth date",
                              date_format="mm.yyyy")
            valid_value = field.validate("13.2010")
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message,
                         "Answer 13.2010 for question Q2 is invalid. Expected date in mm.yyyy format")

        with self.assertRaises(IncorrectDate) as e:
            field = DateField(name="Age", code="Q2", label="What is your birth date",
                              date_format="dd.mm.yyyy")
            valid_value = field.validate("33.12.2010")
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message,
                         "Answer 33.12.2010 for question Q2 is invalid. Expected date in dd.mm.yyyy format")

        with self.assertRaises(IncorrectDate) as e:
            field = DateField(name="Age", code="Q2", label="What is your birth date",
                              date_format="mm.dd.yyyy")
            valid_value = field.validate("13.01.2010")
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message,
                         "Answer 13.01.2010 for question Q2 is invalid. Expected date in mm.dd.yyyy format")

    def test_should_validate_single_answer(self):
        with self.assertRaises(AnswerHasTooManyValuesException) as e:
            clinic_field = SelectField(name="clinic type", code="Q1", label="What type of clinic is it?",
                                       options=["village", "urban"], single_select_flag=True)
            clinic_field.validate("vu")
        self.assertEqual(e.exception.message, "Answer vu for question Q1 contains more than one value.")


    def test_should_throw_exception_if_field_created_with_none_datadict_type(self):
        with self.assertRaises(AssertionError):
            TextField(name="Name", code="Q1", label="What is your Name",
                      constraints=dict(length=TextLengthConstraint(min=4, max=15)))

    def test_should_return_default_language_text(self):
        expected_json = {
            "choices": [{"text": "Lake"}, {"text": "Dam"}],
            "name": "type",
            "parent_field_code": None,
            "type": "select1",
            "code": "T",
            "label": "What type?",
            "required": True,
            "instruction": "test",
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None

        }
        field = SelectField(name="type", code="T", label="What type?",
                            options=[{"text": "Lake"}, {"text": "Dam"}],
                             instruction="test",
                            single_select_flag=True)
        actual_json = field._to_json_view()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_location_field_type_for_default_english_language(self):
        expected_json = {
            "label": "Where do you stay?",
            "name": "field1_Loc",
            "code": "Q1",
            "type": "geocode",
            "parent_field_code": None,
            "required": True,
            "instruction": "test_instruction",
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?",
                             instruction="test_instruction", )
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)
        field.set_value(field.validate("23,23"))
        self.assertEqual("23.0, 23.0", field.convert_to_unicode())

    def test_should_validate_location(self):
        expect_lat_long = (89.1, 100.1)
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?")
        actual_lat_long = field.validate(lat_long_string="89.1 100.1")
        self.assertEqual(expect_lat_long, actual_lat_long)

    def test_should_validate_location_with_whitespaces(self):
        expect_lat_long = (89.1, 100.1)
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?")
        actual_lat_long = field.validate(lat_long_string="89.1    100.1")
        self.assertEqual(expect_lat_long, actual_lat_long)

    def test_should_give_error_for_invalid_location(self):
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?")
        with self.assertRaises(GeoCodeFormatException) as e:
            field.validate(lat_long_string="89.1")
            self.assertEquals(("89.1",), e.exception.data)
        with self.assertRaises(RequiredFieldNotPresentException):
            field.validate(lat_long_string="   ")
        with self.assertRaises(RequiredFieldNotPresentException):
            field.validate(lat_long_string="")
        with self.assertRaises(RequiredFieldNotPresentException):
            field.validate(lat_long_string=None)

    def test_should_convert_field_without_constraints_to_json(self):
        field = TextField(name="Test", code="AA", label="test")
        expected_json = {
            "code": "AA",
            "name": "Test",
            "defaultValue": "",
            "instruction": None,
            "label": "test",
            "parent_field_code": None,
            "type": "text",
            "required": True,
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        self.assertEqual(expected_json, field_to_json(field))

    def test_should_convert_field_with_constraints_to_json(self):
        constraints = [TextLengthConstraint(min=10, max=12), RegexConstraint("^[A-Za-z0-9]+$")]
        field = TextField(name="test", code='MC', label='question', constraints=constraints)
        expected_json = {
            "code": "MC",
            "name": "test",
            "defaultValue": "",
            "instruction": None,
            "label": "question",
            "type": "text",
            'parent_field_code': None,
            "length": {'max': 12, 'min': 10},
            "regex": "^[A-Za-z0-9]+$",
            "required": True,
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }

        self.assertEqual(expected_json, field_to_json(field))

    def test_should_convert_field_with_apostrophe_to_json(self):
        field = TextField(name="Test's", code="AA", label="test")
        expected_json = {
            "code": "AA",
            "name": "Test\'s",
            "defaultValue": "",
            "instruction": None,
            "parent_field_code": None,
            "label": "test",
            "type": "text",
            "required": True,
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        self.assertEqual(expected_json, field_to_json(field))

    def test_should_create_text_field_with_multiple_constraints(self):
        length_constraint = TextLengthConstraint(min=10, max=12)
        regex_constraint = RegexConstraint("^[A-Za-z0-9]+$")
        constraints = [length_constraint, regex_constraint]
        field = TextField(name="test", code='MC', label='question', constraints=constraints)

        self.assertEqual(constraints, field.constraints)

    def test_should_validate_text_data_based_on_list_of_constraints(self):
        length_constraint = TextLengthConstraint(min=10, max=12)
        regex_constraint = RegexConstraint("^[A-Za-z0-9]+$")
        constraints = [length_constraint, regex_constraint]
        field = TextField(name="test", code='MC', label='question', constraints=constraints)

        self.assertEqual('validatable', field.validate('validatable'))
        self.assertRaises(RegexMismatchException, field.validate, '!alidatabl!')
        self.assertRaises(AnswerTooShortException, field.validate, 'val')
        self.assertRaises(AnswerTooLongException, field.validate, 'val11111111111111')

    def test_telephone_number_field_should_return_expected_json(self):
        mobile_number_length = TextLengthConstraint(max=15)
        mobile_number_pattern = RegexConstraint(reg='^[0-9]+$')
        field = TelephoneNumberField(name="test", code='MC', label='question',
                                     constraints=[mobile_number_length, mobile_number_pattern], instruction='')
        expected_json = {
            "label": "question",
            "name": "test",
            "code": "MC",
            'parent_field_code': None,
            "type": "telephone_number",
            "instruction": "",
            "constraints": [('length', {'max': 15}), ('regex', '^[0-9]+$')],
            "defaultValue": '',
            "required": True,
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        self.assertEqual(expected_json, field._to_json())

    def test_should_create_telephone_number_field_from_dictionary(self):
        LABEL = "test"
        field_json = {
            "defaultValue": "",
            "label": LABEL,
            "name": "field1_Name",
            "code": "Q1",
            "type": "telephone_number",
            "constraints": [("length", {"min": 1, "max": 10}), ('regex', '^[0-9]+$')],
            "instruction": "some instruction",
            "required": False
        }
        created_field = field.create_question_from(field_json, self.dbm)

        self.assertIsInstance(created_field, TelephoneNumberField)
        self.assertIsInstance(created_field.constraints[0], TextLengthConstraint)
        self.assertIsInstance(created_field.constraints[1], RegexConstraint)
        self.assertEqual(created_field.constraints[0].max, 10)
        self.assertEqual(created_field.constraints[0].min, 1)
        self.assertEqual(created_field.label, LABEL)
        self.assertEqual(created_field.instruction, "some instruction")
        self.assertFalse(created_field.is_required())

    def test_telephone_number_should_clean_value_to_remove_only_hyphen_from_the_given_value(self):
        mobile_number_length = TextLengthConstraint(max=15)
        mobile_number_pattern = RegexConstraint(reg='^[0-9]+$')
        field = TelephoneNumberField(name="test", code='MC', label='question',
                                     constraints=[mobile_number_length, mobile_number_pattern], instruction='')

        self.assertEqual('1234321122', field._clean('123-4321122'))
        self.assertEqual('123dsasa4321122', field._clean('123dsasa4321122'))

    def test_should_convert_text_in_epsilon_format_to_expanded_text(self):
        mobile_number_length = TextLengthConstraint(max=15)
        mobile_number_pattern = RegexConstraint(reg='^[0-9]+$')
        field = TelephoneNumberField(name="test", code='MC', label='question',
                                     constraints=[mobile_number_length, mobile_number_pattern], instruction='')

        self.assertEqual(u'266123321435', field._clean(u'2.66123321435e+11'))

    def test_telephone_number_should_clean_before_validate(self):
        mobile_number_length = TextLengthConstraint(max=15)
        mobile_number_pattern = RegexConstraint(reg='^[0-9]+$')
        field = TelephoneNumberField(name="test", code='MC', label='question',
                                     constraints=[mobile_number_length, mobile_number_pattern], instruction='')

        self.assertEqual(u'266123321435', field.validate(u'2.66123321435e+11'))
        self.assertEqual(u'266123321435', field.validate(u'266-123321435'))
        self.assertEqual(u'266123321435', field.validate(u'266123321435.0'))

    def test_telephone_number_should_not_trim_the_leading_zeroes(self):
        field = TelephoneNumberField(name="test", code='MC', label='question',
                                     constraints=[], instruction='')
        self.assertEqual(u'020', field.validate(u'020'))

    def test_should_raise_regex_mismatch_exception_if_invalid_phone_number(self):
        mobile_number_length = TextLengthConstraint(max=15)
        mobile_number_pattern = RegexConstraint(reg='^[0-9]+$')
        field = TelephoneNumberField(name="test", code='MC', label='question',
                                     constraints=[mobile_number_length, mobile_number_pattern], instruction='')
        with self.assertRaises(RegexMismatchException):
            field.validate(u'020321dsa')

    def test_field_should_be_required_by_default(self):
        field = TextField(name='text_field', code=None, label=None)
        self.assertTrue(field.is_required())

    def test_field_should_be_set_as_optional(self):
        field = TextField(name='text_field', code=None, label=None, required=False)
        self.assertFalse(field.is_required())

    def test_should_validate_for_required_field(self):
        field = TextField(name='text_field', code=None, label=None)
        with self.assertRaises(RequiredFieldNotPresentException):
            field.validate(None)
        with self.assertRaises(RequiredFieldNotPresentException):
            field.validate("")
        with self.assertRaises(RequiredFieldNotPresentException):
            field.validate("  ")


    def test_date_field_with_event_time_flag_should_return_expected_json(self):
        field = DateField('event_time', 'et', 'event_time', '%m.%d.%Y')
        expected_json = {
            "instruction": None,
            "label": "event_time",
            "name": "event_time",
            "code": "et",
            'parent_field_code': None,
            "type": "date",
            "date_format": "%m.%d.%Y",
            "required": True,
            "appearance": None,
            "constraint_message": None,
            "default": None,
            "hint": None
        }
        self.assertEqual(expected_json, field._to_json())

    def test_should_add_all_xform_constraints(self):
        first_constraint = Mock()
        first_constraint.xform_constraint.return_value = "first"
        second_constraint = Mock()
        second_constraint.xform_constraint.return_value = "second"

        field = Field(constraints=[first_constraint, second_constraint])
        self.assertEqual("first and second", field.xform_constraints())

    def test_should_not_include_none_or_empty_constraints(self):
        first_constraint = Mock()
        first_constraint.xform_constraint.return_value = "first"
        second_constraint = Mock()
        second_constraint.xform_constraint.return_value = None
        third_constraint = Mock()
        third_constraint.xform_constraint.return_value = ""

        field = Field(constraints=[first_constraint, second_constraint, third_constraint])
        self.assertEqual("first", field.xform_constraints())

    def test_should_split_gps_field_based_on_comma(self):
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?",
                             instruction="test_instruction", )
        expected = (12.32, 14.32)
        seperated_values = field.formatted_field_values_for_excel('12.32,14.32')
        self.assertEqual(expected, seperated_values)

    def test_should_split_gps_irrespective_of_space_after_comma(self):
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?",
                             instruction="test_instruction", )

        expected = (12.32, 14.32)
        seperated_values = field.formatted_field_values_for_excel('12.32,   14.32')
        self.assertEqual(expected, seperated_values)


    def test_use_default_format_when_provided_format_not_found(self):
        expected_date_string = 'Feb. 24, 2013, 12:45 PM'
        input_date = datetime.strptime(expected_date_string, '%b. %d, %Y, %H:%M %p')
        actual_date_string = ExcelDate(input_date, 'submission_date').date_as_string()
        self.assertEqual(expected_date_string, actual_date_string)


class TestUniqueIdField(unittest.TestCase):

    def test_should_generate_unicode_value_when_value_present(self):

        field = UniqueIdField("unique_id_type", "name", "q1", "label")
        field.value = "cli001"
        self.assertEqual(field.stringify(), "Unique_id_type(cli001)")


class TestTextField(unittest.TestCase):

    def test_should_update_value_to_empty_string_when_calculated_value_is_NaN(self):

        field = TextField(name='height_calculate', code='height_calculate', label='My calculated question',
                          is_calculated=True)

        field.set_value("NaN")

        self.assertEqual(field.value, "")

    def test_should_retain_value_when_calculated_value_is_not_NaN(self):

        field = TextField(name='height_calculate', code='height_calculate', label='My calculated question',
                          is_calculated=True)

        field.set_value("calculate_value")

        self.assertEqual(field.value, "calculate_value")

