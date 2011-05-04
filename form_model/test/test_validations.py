import unittest
from mangrove.form_model.validation import IntegerConstraint
from mangrove.utils.types import is_empty

class TestValidations(unittest.TestCase):

    def test_should_return_min_max_as_dictionary(self):
        expected_dict={"min":10,"max":20}
        constraint = IntegerConstraint(min=10, max=20)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict,actual_dict)

    def test_should_return_max_as_dictionary(self):
        expected_dict={"max":20}
        constraint = IntegerConstraint(min=None, max=20)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict,actual_dict)

    def test_should_return_min_as_dictionary(self):
        expected_dict={"min":1}
        constraint = IntegerConstraint(min=1)
        actual_dict = constraint._to_json()
        self.assertEqual(expected_dict,actual_dict)

    def test_should_return_min_as_dictionary(self):
        constraint = IntegerConstraint()
        actual_dict = constraint._to_json()
        self.assertTrue(is_empty(actual_dict))
