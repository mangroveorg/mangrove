# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.errors.MangroveException import AnswerHasTooManyValuesException, AnswerHasNoValuesException, AnswerNotInListException, LatitudeNotFloat, LongitudeNotFloat, LatitudeNotInRange, LongitudeNotInRange, RegexMismatchException
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint, ChoiceConstraint, GeoCodeConstraint, RegexConstraint, ConstraintTypes, ConstraintAttributes, constraints_factory
from mangrove.utils.types import is_empty
from mangrove.validate import VdtValueTooBigError, VdtValueTooSmallError, VdtValueTooLongError, VdtValueTooShortError, VdtTypeError


class TestIntegerValidations(unittest.TestCase):
    def test_should_return_min_max_as_dictionary_for_integer(self):
        expected_value = ('range', {"min": 10, "max": 20})
        constraint = NumericRangeConstraint(min=10, max=20)
        actual_value = constraint._to_json()
        self.assertEqual(expected_value, actual_value)

    def test_should_return_max_as_dictionary(self):
        expected_value = ('range', {"max": 20})
        constraint = NumericRangeConstraint(min=None, max=20)
        actual_value = constraint._to_json()
        self.assertEqual(expected_value, actual_value)

    def test_should_return_min_as_dictionary(self):
        expected_value = ('range', {"min": 1})
        constraint = NumericRangeConstraint(min=1)
        actual_value = constraint._to_json()
        self.assertEqual(expected_value, actual_value)

    def test_should_return_empty_dict_for_empty_integer_constraint(self):
        constraint = NumericRangeConstraint() #First off there should not be an empty NumericConstraint
        actual_value = constraint._to_json()
        self.assertTrue(is_empty(actual_value[1]))

    def test_should_validate_range(self):
        constraint = NumericRangeConstraint(min=10, max=20)
        valid_data = constraint.validate(15)
        self.assertEqual(valid_data, 15)
        valid_data = constraint.validate("15")
        self.assertEqual(valid_data, 15)

    def test_should_raise_exception_for_integer_above_range(self):
        with self.assertRaises(VdtValueTooBigError):
            constraint = NumericRangeConstraint(min=10, max=20)
            constraint.validate(21)

    def test_should_raise_exception_for_integer_below_range(self):
        with self.assertRaises(VdtValueTooSmallError):
            constraint = NumericRangeConstraint(min=10, max=20)
            constraint.validate(1)

    def test_should_raise_exception_for_non_integer_value(self):
        with self.assertRaises(VdtTypeError):
            constraint = NumericRangeConstraint(min=10, max=20)
            constraint.validate("asasd")


class TestTextValidations(unittest.TestCase):
    def test_should_return_min_max_as_dictionary_for_integer(self):
        expected_dict = ('length', {"min": 10, "max": 20})
        constraint = TextLengthConstraint(min=10, max=20)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_max_as_dictionary(self):
        expected_dict = ('length', {'max': 20})
        constraint = TextLengthConstraint(min=None, max=20)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_min_as_dictionary(self):
        expected_dict = ('length', {'min': 1})
        constraint = TextLengthConstraint(min=1)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict, actual_dict)

    def test_should_return_empty_dict_for_empty_text_constraint(self):
        constraint = TextLengthConstraint()
        actual_dict = constraint._to_json()
        self.assertTrue(is_empty(actual_dict))

    def test_should_validate_range(self):
        constraint = TextLengthConstraint(min=10, max=20)
        valid_data = constraint.validate("valid_string")
        self.assertEqual(valid_data, "valid_string")

    def test_should_raise_exception_for_integer_above_range(self):
        with self.assertRaises(VdtValueTooLongError):
            constraint = TextLengthConstraint(min=1, max=4)
            constraint.validate("invalid_string")

    def test_should_raise_exception_for_integer_below_range(self):
        with self.assertRaises(VdtValueTooShortError):
            constraint = TextLengthConstraint(min=10, max=20)
            constraint.validate("small")

    def test_should_validate_range_and_strip_text(self):
        constraint = TextLengthConstraint(min=10, max=20)
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
        constraint = GeoCodeConstraint()
        expected_response = (90.0, 130.0)
        actual_response = constraint.validate("90", "130")
        self.assertEqual(expected_response, actual_response)

    def test_should_invalidate_non_float_latitude(self):
        with self.assertRaises(LatitudeNotFloat) as e:
            constraint = GeoCodeConstraint()
            constraint.validate("a", "1.2")

        self.assertEqual(("a",), e.exception.data)

    def test_should_invalidate_non_float_longitude(self):
        with self.assertRaises(LongitudeNotFloat) as e:
            constraint = GeoCodeConstraint()
            constraint.validate("1.2", "asasasas")
        self.assertEqual(("asasasas",), e.exception.data)

    def test_latitude_should_be_between_minus_90_and_90(self):
        with self.assertRaises(LatitudeNotInRange) as e:
            constraint = GeoCodeConstraint()
            constraint.validate("100", "90")
        self.assertEqual(("100",), e.exception.data)
        with self.assertRaises(LatitudeNotInRange) as e:
            constraint = GeoCodeConstraint()
            constraint.validate("-100", "90")
        self.assertEqual(("-100",), e.exception.data)


    def test_longitude_should_be_between_minus_180_and_180(self):
        with self.assertRaises(LongitudeNotInRange) as e:
            constraint = GeoCodeConstraint()
            constraint.validate("-10", "190")
        self.assertEqual(("190",), e.exception.data)
        with self.assertRaises(LongitudeNotInRange) as e:
            constraint = GeoCodeConstraint()
            constraint.validate("90", "-190")
        self.assertEqual(("-190",), e.exception.data)

    def test_should_strip_white_spaces(self):
        constraint = GeoCodeConstraint()
        self.assertEqual((90.0, 130.0), constraint.validate("90 ", " 130"))
        self.assertEqual((90.0, 130.0), constraint.validate("   90 ", " 130  "))

    def test_should_remove_right_to_left_mark_character_while_importing_from_excel(self):
        constraint = GeoCodeConstraint()
        # the string is '49.418607\u200e'
        self.assertEqual((90.0, 49.418607), constraint.validate("90 ", u'49.418607‎'))
        self.assertEqual((49.418607, 130.0), constraint.validate(u'49.418607‎', " 130  "))

    def test_should_raise_error_for_non_ascii_characters(self):
        # the string is '49.418607\u200e'
        with self.assertRaises(UnicodeEncodeError) as e:
            constraint = GeoCodeConstraint()
            constraint.validate(u'23º', u'43º')
        self.assertEqual("ordinal not in range(128)", e.exception.reason)


class TestRegexValidations(unittest.TestCase):
    def test_should_validate_values_within_regex(self):
        constraint = RegexConstraint(reg="^[A-Za-z0-9]+$")
        self.assertEqual("Hello1", constraint.validate("Hello1"))

    def test_should_throw_error_on_invalid_value(self):
        constraint = RegexConstraint(reg="^[A-Za-z0-9]+$")
        with self.assertRaises(RegexMismatchException):
            constraint.validate("Hello 1")

    def test_should_return_valid_regex_json(self):
        pattern = "^[A-Za-z0-9]+$"
        constraint = RegexConstraint(reg=pattern)
        self.assertEqual(("regex", pattern), constraint._to_json())


class TestCreationOfConstraints(unittest.TestCase):
    def test_should_create_a_constraint_dictionary(self):
        constraint_info = [
            (ConstraintTypes.LENGTH, {ConstraintAttributes.MIN: 10, ConstraintAttributes.MAX: 20}),
            (ConstraintTypes.REGEX, "^\w")
        ]
        constraints = constraints_factory(constraint_info)
        self.assertEqual(2, len(constraints))

    def test_should_create_empty_constraint_dictionary_if_None(self):
        constraint_info = []
        constraints = constraints_factory(constraint_info)
        self.assertEqual([], constraints)

    def test_should_throw_error_if_constraint_not_known(self):
        constraint_info = [('nonsense', 'this should bomb'), ('regex', '^$')]
        constraints = constraints_factory(constraint_info)
        self.assertEqual(1, len(constraints))
        self.assertTrue(isinstance(constraints[0], RegexConstraint))
