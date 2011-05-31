# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.errors.MangroveException import AnswerHasTooManyValuesException, AnswerHasNoValuesException, AnswerNotInListException, LatitudeNotFloat, LongitudeNotFloat, LatitudeNotInRange, LongitudeNotInRange
from mangrove.form_model.validation import NumericConstraint, TextConstraint, ChoiceConstraint, LocationConstraint
from mangrove.utils.types import is_empty
from validate import VdtValueTooBigError, VdtValueTooSmallError, VdtValueTooLongError, VdtValueTooShortError, VdtTypeError


class TestIntegerValidations(unittest.TestCase):
    def test_should_return_min_max_as_dictionary_for_integer(self):
        expected_dict = {"min": 10, "max": 20}
        constraint = NumericConstraint(min=10, max=20)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_max_as_dictionary(self):
        expected_dict = {"max": 20}
        constraint = NumericConstraint(min=None, max=20)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_min_as_dictionary(self):
        expected_dict = {"min": 1}
        constraint = NumericConstraint(min=1)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_empty_dict_for_empty_integer_constraint(self):
        constraint = NumericConstraint()
        actual_dict = constraint._to_json()
        self.assertTrue(is_empty(actual_dict))

    def test_should_validate_range(self):
        constraint = NumericConstraint(min=10, max=20)
        valid_data = constraint.validate(15)
        self.assertEqual(valid_data, 15)
        valid_data = constraint.validate("15")
        self.assertEqual(valid_data, 15)

    def test_should_raise_exception_for_integer_above_range(self):
        with self.assertRaises(VdtValueTooBigError):
            constraint = NumericConstraint(min=10, max=20)
            constraint.validate(21)

    def test_should_raise_exception_for_integer_below_range(self):
        with self.assertRaises(VdtValueTooSmallError):
            constraint = NumericConstraint(min=10, max=20)
            constraint.validate(1)

    def test_should_raise_exception_for_non_integer_value(self):
        with self.assertRaises(VdtTypeError):
            constraint = NumericConstraint(min=10, max=20)
            constraint.validate("asasd")


class TestTextValidations(unittest.TestCase):
    def test_should_return_min_max_as_dictionary_for_integer(self):
        expected_dict = {"min": 10, "max": 20}
        constraint = TextConstraint(min=10, max=20)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_max_as_dictionary(self):
        expected_dict = {"max": 20}
        constraint = TextConstraint(min=None, max=20)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_min_as_dictionary(self):
        expected_dict = {"min": 1}
        constraint = TextConstraint(min=1)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_empty_dict_for_empty_text_constraint(self):
        constraint = TextConstraint()
        actual_dict = constraint._to_json()
        self.assertTrue(is_empty(actual_dict))

    def test_should_validate_range(self):
        constraint = TextConstraint(min=10, max=20)
        valid_data = constraint.validate("valid_string")
        self.assertEqual(valid_data, "valid_string")

    def test_should_raise_exception_for_integer_above_range(self):
        with self.assertRaises(VdtValueTooLongError):
            constraint = TextConstraint(min=1, max=4)
            constraint.validate("invalid_string")

    def test_should_raise_exception_for_integer_below_range(self):
        with self.assertRaises(VdtValueTooShortError):
            constraint = TextConstraint(min=10, max=20)
            constraint.validate("small")

    def test_should_validate_range_and_strip_text(self):
        constraint = TextConstraint(min=10, max=20)
        valid_data = constraint.validate("valid_string      ")
        self.assertEqual(valid_data, "valid_string")


class TestChoiceValidations(unittest.TestCase):
    def test_should_validate_multiple_choice(self):
        constraint = ChoiceConstraint(single_select_constraint=False, list_of_valid_choices=["village", "urban"],
                                      code="Q1")
        v_data = constraint.validate("ab")
        self.assertEquals(v_data, ["village", "urban"])

    def test_should_not_validate_wrong_choice(self):
        with self.assertRaises(AnswerNotInListException):
            constraint = ChoiceConstraint(single_select_constraint=True, list_of_valid_choices=["village", "urban"],
                                          code="Q1")
            constraint.validate("c")

    def test_should_not_validate_multiple_values_sent_for_single_choice(self):
        with self.assertRaises(AnswerHasTooManyValuesException):
            constraint = ChoiceConstraint(single_select_constraint=True, list_of_valid_choices=["village", "urban"],
                                          code="Q1")
            constraint.validate("ab")

    def test_should_not_validate_no_values_sent_for_choice(self):
        with self.assertRaises(AnswerHasNoValuesException):
            constraint = ChoiceConstraint(single_select_constraint=True, list_of_valid_choices=["village", "urban"],
                                          code="Q1")
            constraint.validate("")

    def test_should_not_validate_numeric_values_sent_for_choice(self):
        with self.assertRaises(AnswerNotInListException):
            constraint = ChoiceConstraint(single_select_constraint=False,
                                          list_of_valid_choices=["village", "urban", "city", "country"],
                                          code="Q1")
            constraint.validate("1b")

    def test_should_invalidate_special_characters_sent_for_choice(self):
        with self.assertRaises(AnswerNotInListException):
            constraint = ChoiceConstraint(single_select_constraint=False,
                                          list_of_valid_choices=["village", "urban", "city", "country"],
                                          code="Q1")
            constraint.validate("a!b")


class TestLocationValidations(unittest.TestCase):
    def test_latitude_and_longitude_is_float(self):
        constraint = LocationConstraint()
        expected_response = (130.0, 90.0)
        actual_response = constraint.validate("90", "130")
        self.assertEqual(expected_response, actual_response)

    def test_should_invalidate_non_float_latitude(self):
        with self.assertRaises(LatitudeNotFloat) as e:
            constraint = LocationConstraint()
            constraint.validate("a", "1.2")

        self.assertEqual(("a",),e.exception.data)

    def test_should_invalidate_non_float_longitude(self):
        with self.assertRaises(LongitudeNotFloat) as e:
            constraint = LocationConstraint()
            constraint.validate("1.2", "asasasas")
        self.assertEqual(("asasasas",), e.exception.data)

    def test_latitude_should_be_between_minus_90_and_90(self):
        with self.assertRaises(LatitudeNotInRange) as e:
            constraint = LocationConstraint()
            constraint.validate("100", "90")
        self.assertEqual(("100",), e.exception.data)
        with self.assertRaises(LatitudeNotInRange) as e:
            constraint = LocationConstraint()
            constraint.validate("-100", "90")
        self.assertEqual(("-100",), e.exception.data)


    def test_longitude_should_be_between_minus_180_and_180(self):
        with self.assertRaises(LongitudeNotInRange) as e:
            constraint = LocationConstraint()
            constraint.validate("-10", "190")
        self.assertEqual(("190",), e.exception.data)
        with self.assertRaises(LongitudeNotInRange) as e:
            constraint = LocationConstraint()
            constraint.validate("90", "-190")
        self.assertEqual(("-190",), e.exception.data)

