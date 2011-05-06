# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.form_model.validation import IntegerConstraint, TextConstraint
from mangrove.utils.types import is_empty
from validate import VdtValueTooBigError, VdtValueTooSmallError, VdtValueTooLongError, VdtValueTooShortError, VdtTypeError


class TestIntegerValidations(unittest.TestCase):
    def test_should_return_min_max_as_dictionary_for_integer(self):
        expected_dict = {"min": 10, "max": 20}
        constraint = IntegerConstraint(min=10, max=20)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_max_as_dictionary(self):
        expected_dict = {"max": 20}
        constraint = IntegerConstraint(min=None, max=20)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_min_as_dictionary(self):
        expected_dict = {"min": 1}
        constraint = IntegerConstraint(min=1)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_empty_dict_for_empty_integer_constraint(self):
        constraint = IntegerConstraint()
        actual_dict = constraint._to_json()
        self.assertTrue(is_empty(actual_dict))

    def test_should_validate_range(self):
        constraint = IntegerConstraint(min=10, max=20)
        valid_data = constraint.validate(15)
        self.assertEqual(valid_data, 15)
        valid_data = constraint.validate("15")
        self.assertEqual(valid_data, 15)

    def test_should_raise_exception_for_integer_above_range(self):
        with self.assertRaises(VdtValueTooBigError):
            constraint = IntegerConstraint(min=10, max=20)
            constraint.validate(21)

    def test_should_raise_exception_for_integer_below_range(self):
        with self.assertRaises(VdtValueTooSmallError):
            constraint = IntegerConstraint(min=10, max=20)
            constraint.validate(1)

    def test_should_raise_exception_for_non_integer_value(self):
        with self.assertRaises(VdtTypeError):
            constraint = IntegerConstraint(min=10, max=20)
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
