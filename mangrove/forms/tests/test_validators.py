# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.errors.MangroveException import AnswerHasTooManyValuesException, AnswerHasNoValuesException, AnswerNotInListException, LatitudeNotFloat, LongitudeNotFloat, LatitudeNotInRange, LongitudeNotInRange, RegexMismatchException, GeoCodeFormatException
from mangrove.forms.validators import NumericRangeValidator, TextLengthValidator, ChoiceValidator, GeoCodeValidator, validator_factory, RegexValidator, SequenceValidator
from mangrove.validate import VdtValueTooBigError, VdtValueTooSmallError, VdtValueTooLongError, VdtValueTooShortError, VdtTypeError


class TestIntegerValidators(unittest.TestCase):

    def test_should_return_min_max_as_dictionary_for_integer(self):
        validator = NumericRangeValidator(min=10, max=20)
        self.assertEqual({'_class': 'NumericRangeValidator', "min": 10, "max": 20}, validator._to_json())

    def test_should_return_max_as_dictionary(self):
        constraint = NumericRangeValidator(max=20)
        self.assertEqual({'max': 20, '_class': 'NumericRangeValidator'}, constraint._to_json())

    def test_should_return_min_as_dictionary(self):
        constraint = NumericRangeValidator(min=1)
        self.assertEqual({'_class': 'NumericRangeValidator',"min": 1}, constraint._to_json())

    def test_should_return_empty_dict_for_empty_integer_constraint(self):
        constraint = NumericRangeValidator() #First off there should not be an empty NumericConstraint
        self.assertEqual({'_class': 'NumericRangeValidator'}, constraint._to_json())

    def test_should_validate_range(self):
        constraint = NumericRangeValidator(min=10, max=20)
        valid_data = constraint.validate(15)
        self.assertEqual(valid_data, 15)
        valid_data = constraint.validate("15")
        self.assertEqual(valid_data, 15)

    def test_should_raise_exception_for_integer_above_range(self):
        with self.assertRaises(VdtValueTooBigError):
            constraint = NumericRangeValidator(min=10, max=20)
            constraint.validate(21)

    def test_should_raise_exception_for_integer_below_range(self):
        with self.assertRaises(VdtValueTooSmallError):
            constraint = NumericRangeValidator(min=10, max=20)
            constraint.validate(1)

    def test_should_raise_exception_for_non_integer_value(self):
        with self.assertRaises(VdtTypeError):
            constraint = NumericRangeValidator(min=10, max=20)
            constraint.validate("asasd")


class TestTextValidator(unittest.TestCase):
    def test_should_return_min_max_as_dictionary_for_integer(self):
        actual_dict = (TextLengthValidator(min=10, max=20))._to_json()
        self.assertEqual({'_class':'TextLengthValidator', "min": 10, "max": 20}, actual_dict)

    def test_should_return_max_as_dictionary(self):
        actual_dict = (TextLengthValidator(max=20))._to_json()
        self.assertEqual({'_class':'TextLengthValidator', 'max': 20}, actual_dict)

    def test_should_return_min_as_dictionary(self):
        self.assertEqual({'_class': 'TextLengthValidator','min': 1}, (TextLengthValidator(min=1))._to_json())

    def test_should_return_empty_dict_for_empty_text_constraint(self):
        self.assertEqual({'_class': 'TextLengthValidator'}, (TextLengthValidator())._to_json())

    def test_should_validate_range(self):
        constraint = TextLengthValidator(min=10, max=20)
        valid_data = constraint.validate("valid_string")
        self.assertEqual(valid_data, "valid_string")

    def test_should_raise_exception_for_integer_above_range(self):
        with self.assertRaises(VdtValueTooLongError):
            constraint = TextLengthValidator(min=1, max=4)
            constraint.validate("invalid_string")

    def test_should_raise_exception_for_integer_below_range(self):
        with self.assertRaises(VdtValueTooShortError):
            constraint = TextLengthValidator(min=10, max=20)
            constraint.validate("small")

    def test_should_validate_range_and_strip_text(self):
        constraint = TextLengthValidator(min=10, max=20)
        self.assertEqual("valid_string", constraint.validate("valid_string      "))


class TestChoiceValidator(unittest.TestCase):
    def test_should_validate_multiple_choice(self):
        constraint = ChoiceValidator(single_select_constraint=False, list_of_valid_choices=["village", "urban"])
        self.assertEquals(["village", "urban"], constraint.validate("ab", "Q1"))

    def test_should_not_validate_wrong_choice(self):
        with self.assertRaises(AnswerNotInListException):
            constraint = ChoiceValidator(single_select_constraint=True, list_of_valid_choices=["village", "urban"])
            constraint.validate("c", "Q1")

    def test_should_not_validate_multiple_values_sent_for_single_choice(self):
        with self.assertRaises(AnswerHasTooManyValuesException):
            constraint = ChoiceValidator(single_select_constraint=True, list_of_valid_choices=["village", "urban"])
            constraint.validate("ab", "Q1")

    def test_should_not_validate_no_values_sent_for_choice(self):
        with self.assertRaises(AnswerHasNoValuesException):
            constraint = ChoiceValidator(single_select_constraint=True, list_of_valid_choices=["village", "urban"])
            constraint.validate("", "Q1")

    def test_should_not_validate_numeric_values_sent_for_choice(self):
        with self.assertRaises(AnswerNotInListException):
            constraint = ChoiceValidator(single_select_constraint=False,
                                          list_of_valid_choices=["village", "urban", "city", "country"])
            constraint.validate("1b", "Q1")

    def test_should_invalidate_special_characters_sent_for_choice(self):
        with self.assertRaises(AnswerNotInListException):
            constraint = ChoiceValidator(single_select_constraint=False,
                                          list_of_valid_choices=["village", "urban", "city", "country"])
            constraint.validate("a!b", "Q1")


class TestLocationValidator(unittest.TestCase):
    def test_latitude_and_longitude_is_float(self):
        constraint = GeoCodeValidator()
        expected_response = (90.0, 130.0)
        actual_response = constraint.validate("90 130")
        self.assertEqual(expected_response, actual_response)

    def test_should_invalidate_non_float_latitude(self):
        with self.assertRaises(LatitudeNotFloat) as e:
            constraint = GeoCodeValidator()
            constraint.validate("a 1.2")

        self.assertEqual(("a",), e.exception.data)

    def test_should_invalidate_non_float_longitude(self):
        with self.assertRaises(LongitudeNotFloat) as e:
            constraint = GeoCodeValidator()
            constraint.validate("1.2 asasasas")
        self.assertEqual(("asasasas",), e.exception.data)

    def test_latitude_should_be_between_minus_90_and_90(self):
        with self.assertRaises(LatitudeNotInRange) as e:
            constraint = GeoCodeValidator()
            constraint.validate("100 90")
        self.assertEqual(("100",), e.exception.data)
        with self.assertRaises(LatitudeNotInRange) as e:
            constraint = GeoCodeValidator()
            constraint.validate("-100 90")
        self.assertEqual(("-100",), e.exception.data)


    def test_longitude_should_be_between_minus_180_and_180(self):
        with self.assertRaises(LongitudeNotInRange) as e:
            constraint = GeoCodeValidator()
            constraint.validate("-10 190")
        self.assertEqual(("190",), e.exception.data)
        with self.assertRaises(LongitudeNotInRange) as e:
            constraint = GeoCodeValidator()
            constraint.validate("90 -190")
        self.assertEqual(("-190",), e.exception.data)

    def test_should_strip_white_spaces(self):
        constraint = GeoCodeValidator()
        self.assertEqual((90.0, 130.0), constraint.validate("90  130"))
        self.assertEqual((90.0, 130.0), constraint.validate("   90  130  "))

    def test_should_remove_right_to_left_mark_character(self):
        constraint = GeoCodeValidator()
        # the string is '49.418607\u200e'
        self.assertEqual((90.0, 49.418607), constraint.validate("90 " + u'49.418607‎'))
        self.assertEqual((49.418607, 130.0), constraint.validate(u'49.418607‎'+ " 130  "))

    def test_should_raise_exception_if_only_either_of_lat_lng_is_submitted(self):
        constraint = GeoCodeValidator()
        with self.assertRaises(GeoCodeFormatException):
            constraint.validate("23")

class TestRegexValidators(unittest.TestCase):
    def test_should_validate_values_within_regex(self):
        validator = RegexValidator("^[A-Za-z0-9]+$")
        self.assertEqual("Hello1", validator.validate("Hello1"))

    def test_should_throw_error_on_invalid_value(self):
        validator = RegexValidator("^[A-Za-z0-9]+$")
        with self.assertRaises(RegexMismatchException):
            validator.validate("Hello 1")

    def test_should_return_valid_regex_json(self):
        pattern = "^[A-Za-z0-9]+$"
        validator = RegexValidator(pattern)
        self.assertEqual({"_class": "RegexValidator", "pattern": pattern}, validator._to_json())


class TestCreationOfConstraints(unittest.TestCase):
    def test_should_create_a_constraint_dictionary(self):
        constraint_info = [
            {"_class":"NumericRangeValidator","min": 10, "max": 20},
            {"_class":"TextLengthValidator","min": 10, "max": 20}
        ]
        constraints = validator_factory(constraint_info)
        self.assertEqual(2, len(constraints))

    def test_should_create_empty_constraint_dictionary_if_None(self):
        constraint_info = []
        constraints = validator_factory(constraint_info)
        self.assertEqual([], constraints)

class TestSequenceValidator(unittest.TestCase):

    def test_should_return_value_if_sequence(self):
        self.assertEqual(["a", "b", "c"], SequenceValidator().validate(["a", "b", "c"]))
        
    def test_should_raise_exception_if_value_is_not_seq(self):
        with self.assertRaises(Exception):
            SequenceValidator().validate("ddsdw")
        