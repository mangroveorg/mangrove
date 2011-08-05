# vim= ai ts=4 sts=4 et sw=4 encoding=utf-8
import json

import unittest
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType

from mangrove.errors.MangroveException import IncorrectDate, GeoCodeFormatException, RegexMismatchException
from mangrove.form_model.field import DateField, GeoCodeField, field_to_json, HierarchyField

from mangrove.errors.MangroveException import AnswerTooBigException, AnswerTooSmallException,\
    AnswerTooLongException, AnswerTooShortException, AnswerWrongType, AnswerHasTooManyValuesException
from mangrove.form_model.field import TextField, IntegerField, SelectField

from mangrove.form_model import field
from mangrove.form_model.validation import NumericConstraint, TextConstraint, RegexConstraint


class TestField(unittest.TestCase):
    def setUp(self):
        self.ddtype = Mock(spec=DataDictType)
        self.DDTYPE_JSON = {'test': 'test'}
        self.ddtype.to_json.return_value = self.DDTYPE_JSON
        self.patcher = patch(target='mangrove.form_model.field.DataDictType', spec=DataDictType)
        self.ddtype_module = self.patcher.start()
        self.dbm = Mock(spec=DatabaseManager)

    def tearDown(self):
        self.patcher.stop()

    def test_should_create_text_field_type_for_default_english_language(self):
        expected_json = {
            "defaultValue": "some default value",
            "label": {"eng": "What is your name"},
            "name": "field1_Name",
            "instruction": "Answer is word or phrase",
            "code": "Q1",
            "constraints": {"length": {"min": 1, "max": 20}},
            "type": "text",
            "ddtype": self.DDTYPE_JSON,
            }
        field = TextField(name="field1_Name", code="Q1", label="What is your name",
                          defaultValue="some default value", constraints={"length":TextConstraint(1, 20)}, language="eng",
                          ddtype=self.ddtype, instruction="Answer is word or phrase")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_list_field_type_for_default_english_language(self):
        expected_json = {
            "label": {"eng": "What is your location"},
            "name": "loc",
            "instruction": "Answer is list",
            "code": "Q1",
            "type": "list",
            "ddtype": self.DDTYPE_JSON,
            }
        field = HierarchyField(name="loc", code="Q1", label="What is your location", language="eng",
                               ddtype=self.ddtype, instruction="Answer is list")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)


    def test_should_create_integer_field_type_for_default_english_language(self):
        expected_json = {
            "label": {"eng": "What is your age"},
            "name": "Age",
            "code": "Q2",
            "range": {},
            "ddtype": self.DDTYPE_JSON,
            "type": "integer",
            "instruction": "test_instruction"
        }
        field = IntegerField(name="Age", code="Q2", label="What is your age",
                             language="eng", ddtype=self.ddtype, instruction="test_instruction")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_integer_field_type_for_default_english_language_with_range(self):
        expected_json = {
            "label": {"eng": "What is your age"},
            "name": "Age",
            "code": "Q2",
            "range": {"min": 15, "max": 120},
            "ddtype": self.DDTYPE_JSON,
            "type": "integer",
            "instruction": "test_instruction"
        }
        field = IntegerField(name="Age", code="Q2", label="What is your age",
                             language="eng", range=NumericConstraint(min=15, max=120), ddtype=self.ddtype,
                             instruction="test_instruction")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_select_one_field_type_for_default_english_language(self):
        expected_json = {
            "label": {"eng": "What is your favorite color"},
            "name": "color",
            "choices": [{"text": {"eng": "RED"}, "val": 1}, {"text": {"eng": "YELLOW"}, "val": 2},
                    {"text": {'eng': 'green'}, "val": 3}],
            "code": "Q3",
            "ddtype": self.DDTYPE_JSON,
            "type": "select1",
            "instruction": None
        }
        field = SelectField(name="color", code="Q3", label="What is your favorite color",
                            language="eng", options=[("RED", 1), ("YELLOW", 2), ('green', 3)], ddtype=self.ddtype)
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_multi_select_field_type_for_default_english_language(self):
        expected_json = {
            "label": {"eng": "What is your favorite color"},
            "name": "color",
            "choices": [{"text": {"eng": "RED"}, "val": 1}, {"text": {"eng": "YELLOW"}, "val": 2},
                    {"text": {'eng': 'green'}}],
            "code": "Q3",
            "ddtype": self.DDTYPE_JSON,
            "type": "select",
            "instruction": "test_instruction"
        }
        field = SelectField(name="color", code="Q3", label="What is your favorite color",
                            language="eng", options=[("RED", 1), ("YELLOW", 2), ('green')], single_select_flag=False,
                            ddtype=self.ddtype, instruction="test_instruction")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_convert_multiple_select_field_to_html(self):
        exptected_html = """<tr><th><label for="q3">color</label></th><td><select name="q3" MULTIPLE size="3"><option value="1">RED</option><option value="2">YELLOW</option><option value="3">green</option></select></td></tr>"""
        field = SelectField(name="color", code="Q3", label="What is your favorite color",
                            language="eng", options=[("RED", 1), ("YELLOW", 2), ('green', 3)], single_select_flag=False,
                            ddtype=self.ddtype, instruction="test_instruction")
        self.assertEqual(exptected_html, field.to_html())

    def test_should_add_label_for_french_language(self):
        expected_json = {
            "defaultValue": "some default value",
            "label": {"eng": "What is your name", "fra": "french label"},
            "name": "field1_Name",
            "code": "Q1",
            "instruction": "test_instruction",
            "ddtype": self.DDTYPE_JSON,
            "type": "text"
        }
        field = TextField(name="field1_Name", code="Q1", label="What is your name",
                          defaultValue="some default value", ddtype=self.ddtype, instruction="test_instruction")
        field.add_or_edit_label(language="fra", label="french label")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_edit_label_for_english_language(self):
        expected_json = {
            "defaultValue": "some default value",
            "label": {"eng": "english label", "fra": "french label"},
            "name": "field1_Name",
            "code": "Q1",
            "ddtype": self.DDTYPE_JSON,
            "type": "text",
            "instruction": "test_instruction",
            }
        field = TextField(name="field1_Name", code="Q1", label="What is your name",
                          defaultValue="some default value", ddtype=self.ddtype, instruction="test_instruction")
        field.add_or_edit_label(language="fra", label="french label")
        field.add_or_edit_label(label="english label")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_add_entity_field(self):
        expected_json = {
            "defaultValue": "",
            "label": {"eng": "What is your name"},
            "name": "field1_Name",
            "code": "Q1",
            "type": "text",
            "ddtype": self.DDTYPE_JSON,
            "entity_question_flag": True,
            "instruction": "test_instruction"
        }
        field = TextField(name="field1_Name", code="Q1", label="What is your name",
                          entity_question_flag=True, ddtype=self.ddtype, instruction="test_instruction")
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_text_field_from_dictionary(self):
        self.ddtype_module.create_from_json.return_value = self.ddtype
        field_json = {
            "defaultValue": "",
            "label": {"eng": "What is your name"},
            "name": "field1_Name",
            "code": "Q1",
            "type": "text",
            "constraints":{ "length":{"min": 1, "max": 10}},
            "entity_field_flag": True,
            "ddtype": self.ddtype,
            "instruction": "some instruction"
        }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, TextField)
        self.assertIsInstance(created_field.constraints["length"], TextConstraint)
        self.assertEqual(created_field.constraints["length"].max, 10)
        self.assertEqual(created_field.constraints["length"].min, 1)
        self.assertEqual(created_field.ddtype, self.ddtype)
        self.assertEqual(created_field.label, {"eng": "What is your name"})
        self.assertEqual(created_field.instruction, "some instruction")

    def test_should_create_integer_field_with_validations(self):
        self.ddtype_module.create_from_json.return_value = self.ddtype
        field_json = {
            "defaultValue": "",
            "label": {"eng": "What is your age"},
            "name": "field1_age",
            "code": "Q1",
            "type": "integer",
            "ddtype": self.DDTYPE_JSON,
            "range": {"min": 0, "max": 100},
            "entity_field_flag": False
        }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, IntegerField)
        self.assertEqual(created_field._dict["range"], {"min": 0, "max": 100})
        self.assertIsInstance(created_field.constraint, NumericConstraint)
        self.assertEqual(created_field.constraint.max, 100)
        self.assertEqual(created_field.constraint.min, 0)
        self.assertEqual(created_field.ddtype, self.ddtype)

    def test_should_create_select_field_with_options(self):
        self.ddtype_module.create_from_json.return_value = self.ddtype
        field_json = {
            "name": "q3",
            "code": "qc3",
            "type": "select",
            "ddtype": self.DDTYPE_JSON,
            "choices": [{"text": {"eng": "option 1"}, "value": "c1"},
                    {"text": {"eng": "option 1"}, "value": "c2"}],
            "entity_field_flag": False}
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, SelectField)
        self.assertEqual(created_field.SINGLE_SELECT_FLAG, False)
        self.assertEqual(created_field.ddtype, self.ddtype)


    def test_should_create_select_field_with_single_select_options(self):
        self.ddtype_module.create_from_json.return_value = self.ddtype
        field_json = {
            "name": "q3",
            "code": "qc3",
            "type": "select1",
            "ddtype": self.DDTYPE_JSON,
            "choices": [{"text": {"eng": "hello", "fr": "bonjour"}, "value": "c1"},
                    {"text": {"eng": "world"}, "value": "c2"}],
            "entity_field_flag": False}

        expected_option_list = [{"text": {"eng": "hello", "fr": "bonjour"}, "value": "c1"},
                {"text": {"eng": "world"}, "value": "c2"}]
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, SelectField)
        self.assertEqual(created_field.SINGLE_SELECT_FLAG, True)
        self.assertEqual(created_field.options, expected_option_list)
        self.assertEqual(created_field.ddtype, self.ddtype)

    def test_should_return_error_for_integer_range_validation(self):
        field = IntegerField(name="Age", code="Q2", label="What is your age",
                             language="eng", range=NumericConstraint(min=15, max=120), ddtype=self.ddtype)
        valid_value = field.validate("120")
        self.assertEqual(valid_value, 120)
        valid_value = field.validate("25.5")
        self.assertEqual(valid_value, 25.5)

    def test_should_return_error_for_wrong_type_for_integer(self):
        with self.assertRaises(AnswerWrongType) as e:
            field = IntegerField(name="Age", code="Q2", label="What is your age",
                                 language="eng", range=NumericConstraint(min=15, max=120), ddtype=self.ddtype)
            field.validate("asas")
        self.assertEqual(e.exception.message, "Answer asas for question Q2 is of the wrong type.")

    def test_should_return_error_for_integer_range_validation_for_max_value(self):
        with self.assertRaises(AnswerTooBigException) as e:
            field = IntegerField(name="Age", code="Q2", label="What is your age",
                                 language="eng", range=NumericConstraint(min=15, max=120), ddtype=self.ddtype)
            valid_value = field.validate(150)
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message, "Answer 150 for question Q2 is greater than allowed.")

    def test_should_return_error_for_integer_range_validation_for_min_value(self):
        with self.assertRaises(AnswerTooSmallException) as e:
            field = IntegerField(name="Age", code="Q2", label="What is your age",
                                 language="eng", range=NumericConstraint(min=15, max=120), ddtype=self.ddtype)
            valid_value = field.validate(11)
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message, "Answer 11 for question Q2 is smaller than allowed.")

    def test_successful_text_length_validation(self):
        field = TextField(name="Name", code="Q2", label="What is your Name",
                          language="eng", constraints=dict(length=TextConstraint(min=4, max=15)), ddtype=self.ddtype)
        field1 = TextField(name="Name", code="Q2", label="What is your Name",
                           language="eng", ddtype=self.ddtype)
        valid_value = field.validate("valid")
        self.assertEqual(valid_value, "valid")
        valid_value = field1.validate("valid")
        self.assertEqual(valid_value, "valid")

    def test_should_return_error_for_text_length_validation_for_max_value(self):
        with self.assertRaises(AnswerTooLongException) as e:
            field = TextField(name="Age", code="Q2", label="What is your age",
                              language="eng", constraints={"length":TextConstraint(min=1, max=4)}, ddtype=self.ddtype)
            valid_value = field.validate("long_answer")
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message, "Answer long_answer for question Q2 is longer than allowed.")

    def test_should_return_error_for_text_length_validation_for_min_value(self):
        with self.assertRaises(AnswerTooShortException) as e:
            field = TextField(name="Age", code="Q2", label="What is your age",
                              language="eng", constraints={'length':TextConstraint(min=15, max=120)}, ddtype=self.ddtype)
            valid_value = field.validate("short")
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message, "Answer short for question Q2 is shorter than allowed.")

    def test_should_create_date_field(self):
        self.ddtype_module.create_from_json.return_value = self.ddtype
        field_json = {
            "defaultValue": "",
            "label": {"eng": "What is your birth date"},
            "name": "Birth_date",
            "code": "Q1",
            "type": "date",
            "date_format": "%m.%Y",
            "ddtype": self.DDTYPE_JSON,
            }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, DateField)
        self.assertEqual(created_field.date_format, "%m.%Y")
        self.assertEqual(created_field.ddtype, self.ddtype)

    def test_should_create_geo_code_field(self):
        self.ddtype_module.create_from_json.return_value = self.ddtype
        field_json = {
            "label": {"eng": "What is your location"},
            "name": "Birth_place",
            "code": "LOC",
            "type": "geocode",
            "ddtype": self.DDTYPE_JSON,
            }
        created_field = field.create_question_from(field_json, self.dbm)
        self.assertIsInstance(created_field, GeoCodeField)
        self.assertEqual(created_field.ddtype, self.ddtype)

    def test_should_return_error_for_incorrect_date_format_error_for_wrong_format(self):
        with self.assertRaises(IncorrectDate) as e:
            field = DateField(name="Age", code="Q2", label="What is your birth date",
                              language="eng", date_format="mm.yyyy", ddtype=self.ddtype)
            valid_value = field.validate("13.2010")
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message,
                         "Answer 13.2010 for question Q2 is invalid. Expected date in mm.yyyy format")

        with self.assertRaises(IncorrectDate) as e:
            field = DateField(name="Age", code="Q2", label="What is your birth date",
                              language="eng", date_format="dd.mm.yyyy", ddtype=self.ddtype)
            valid_value = field.validate("33.12.2010")
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message,
                         "Answer 33.12.2010 for question Q2 is invalid. Expected date in dd.mm.yyyy format")

        with self.assertRaises(IncorrectDate) as e:
            field = DateField(name="Age", code="Q2", label="What is your birth date",
                              language="eng", date_format="mm.dd.yyyy", ddtype=self.ddtype)
            valid_value = field.validate("13.01.2010")
            self.assertFalse(valid_value)
        self.assertEqual(e.exception.message,
                         "Answer 13.01.2010 for question Q2 is invalid. Expected date in mm.dd.yyyy format")

    def test_should_validate_single_answer(self):
        with self.assertRaises(AnswerHasTooManyValuesException) as e:
            clinic_field = SelectField(name="clinic type", code="Q1", label="What type of clinic is it?",
                                       language="eng", options=["village", "urban"], single_select_flag=True,
                                       ddtype=self.ddtype)
            clinic_field.validate("vu")
        self.assertEqual(e.exception.message, "Answer vu for question Q1 contains more than one value.")


    def test_should_create_field_with_datadict_type(self):
        nameType = Mock(spec=DataDictType)
        field1 = TextField(name="Name", code="Q1", label="What is your Name",
                           language="eng", constraints=dict(length=TextConstraint(min=4, max=15)), ddtype=nameType)
        self.assertEqual(nameType, field1.ddtype)

        ageType = Mock(spec=DataDictType)
        field2 = IntegerField(name="Age", code="Q2", label="What is your age",
                              language="eng", range=NumericConstraint(min=4, max=15), ddtype=ageType)
        self.assertEqual(ageType, field2.ddtype)

        selectType = Mock(spec=DataDictType)
        field3 = SelectField(name="clinic type", code="Q1", label="What type of clinic is it?",
                             language="eng", options=["village", "urban"], ddtype=selectType)

        self.assertEqual(selectType, field3.ddtype)

        dateType = Mock(spec=DataDictType)
        field4 = DateField(name="Age", code="Q2", label="What is your birth date",
                           language="eng", date_format="%m.%d.%Y", ddtype=dateType)
        self.assertEqual(dateType, field4.ddtype)


    def test_should_throw_exception_if_field_created_with_none_datadict_type(self):
        with self.assertRaises(AssertionError):
            TextField(name="Name", code="Q1", label="What is your Name",
                      language="eng", constraints=dict(length=TextConstraint(min=4, max=15)), ddtype=None)

    def test_should_convert_ddtype_to_json(self):
        expected_json = {
            "defaultValue": "",
            "label": {"eng": "What is your name"},
            "name": "field1_Name",
            "code": "Q1",
            "type": "text",
            "ddtype": self.DDTYPE_JSON,
            "entity_question_flag": True,
            "instruction": None
        }
        field = TextField(name="field1_Name", code="Q1", label="What is your name",
                          entity_question_flag=True, ddtype=self.ddtype)
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)
        self.assertEqual(self.ddtype, field.ddtype)

    def test_should_return_default_language_text(self):
        expected_json = {
            "choices": [{"text": "Lake", "val": None}, {"text": "Dam", "val": None}],
            "name": "type",
            "ddtype": self.DDTYPE_JSON,
            "type": "select1",
            "code": "T",
            "label": {"eng": "What type?"},
            "instruction": "test",

            }
        field = SelectField(name="type", code="T", label="What type?",
                            options=[{"text": {"fr": "lake", "eng": "Lake"}}, {"text": {"fr": "dam", "eng": "Dam"}}],
                            ddtype=self.ddtype, instruction="test",
                            language="eng",
                            single_select_flag=True)
        actual_json = field._to_json_view()
        self.assertEqual(actual_json, expected_json)

    def test_should_create_location_field_type_for_default_english_language(self):
        expected_json = {
            "label": {"eng": "Where do you stay?"},
            "name": "field1_Loc",
            "code": "Q1",
            "type": "geocode",
            "ddtype": self.DDTYPE_JSON,
            "instruction": "test_instruction"
        }
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?", ddtype=self.ddtype,
                             language="eng", instruction="test_instruction", )
        actual_json = field._to_json()
        self.assertEqual(actual_json, expected_json)

    def test_should_validate_location(self):
        expect_lat_long = (89.1, 100.1)
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?", ddtype=self.ddtype,
                             language="eng")
        actual_lat_long = field.validate(lat_long_string="89.1 100.1")
        self.assertEqual(expect_lat_long, actual_lat_long)

    def test_should_validate_location_with_whitespaces(self):
        expect_lat_long = (89.1, 100.1)
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?", ddtype=self.ddtype,
                             language="eng")
        actual_lat_long = field.validate(lat_long_string=" 89.1    100.1  ")
        self.assertEqual(expect_lat_long, actual_lat_long)

    def test_should_give_error_for_invalid_location(self):
        field = GeoCodeField(name="field1_Loc", code="Q1", label="Where do you stay?", ddtype=self.ddtype,
                             language="eng")
        with self.assertRaises(GeoCodeFormatException) as e:
            field.validate(lat_long_string="89.1")
            self.assertEquals(("89.1",), e.exception.data)
        with self.assertRaises(GeoCodeFormatException):
            field.validate(lat_long_string="   ")
        with self.assertRaises(GeoCodeFormatException):
            field.validate(lat_long_string="")
        with self.assertRaises(GeoCodeFormatException):
            field.validate(lat_long_string=None)

    def test_should_convert_field_without_constraints_to_json(self):
        field = TextField(name="Test", code="AA", label="test", ddtype=self.ddtype)
        expected_json = {"code": "AA", "name": "Test", "defaultValue": "", "instruction": None, "label": {"eng": "test"}, "ddtype": {"test": "test"}, "type": "text"}
        self.assertEqual(expected_json, field_to_json(field))

    def test_should_convert_field_with_constraints_to_json(self):
        constraints = {"length": (TextConstraint(min=10, max=12)), "regex": (RegexConstraint("^[A-Za-z0-9]+$"))}
        field = TextField(name="test", code='MC', label='question', ddtype=self.ddtype, constraints=constraints)
        expected_json = {"code": "MC", "name": "test", "defaultValue": "", "instruction": None, "label": {"eng": "question"}, "ddtype": {"test": "test"}, "type": "text",
                         "length":{'max':12, 'min':10}, "regex":"^[A-Za-z0-9]+$"}

        self.assertEqual(expected_json, field_to_json(field))

    def test_should_convert_field_with_apostrophe_to_json(self):
        field = TextField(name="Test's", code="AA", label="test", ddtype=self.ddtype)
        expected_json = {"code": "AA", "name": "Test\'s", "defaultValue": "", "instruction": None, "label": {"eng": "test"}, "ddtype": {"test": "test"}, "type": "text"}
        self.assertEqual(expected_json, field_to_json(field))

    def test_should_create_text_field_with_multiple_constraints(self):
        length_constraint = TextConstraint(min=10, max=12)
        regex_constraint = RegexConstraint("^[A-Za-z0-9]+$")
        constraints = {"length":length_constraint, "regex":regex_constraint}
        field = TextField(name="test", code='MC', label='question', ddtype=self.ddtype, constraints=constraints)

        self.assertEqual(constraints, field.constraints)

    def test_should_validate_text_data_based_on_list_of_constraints(self):
        length_constraint = TextConstraint(min=10, max=12)
        regex_constraint = RegexConstraint("^[A-Za-z0-9]+$")
        constraints = {"length":length_constraint, "regex":regex_constraint}
        field = TextField(name="test", code='MC', label='question', ddtype=self.ddtype, constraints=constraints)

        self.assertEqual('validatable', field.validate('validatable'))
        self.assertRaises(RegexMismatchException,field.validate,'!alidatabl!')
        self.assertRaises(AnswerTooShortException,field.validate,'val')
        self.assertRaises(AnswerTooLongException,field.validate,'val11111111111111')


