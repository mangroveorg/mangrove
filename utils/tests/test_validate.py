import unittest
from mangrove.utils.validate import is_integer, VdtTypeError, VdtValueTooBigError, VdtValueTooSmallError, is_string, VdtValueTooShortError, VdtValueTooLongError, is_string_list, is_option, is_option_in_list

class TestValidate(unittest.TestCase):
    def setUp(self):
        pass

    def test_should_validate_integer(self):
        i=10
        isvalid = is_integer(i)
        self.assertTrue(isvalid)

    def test_should_raise_exception_for_invalid_integer(self):
        with self.assertRaises(VdtTypeError):
            i="as"
            is_integer(i)

    def test_should_validate_range(self):
        i=10
        min_range = 0
        max_range = 11
        isvalid = is_integer(i, min_range, max_range)
        self.assertTrue(isvalid)

    def test_should_raise_exception_for_integer_above_range(self):
        with self.assertRaises(VdtValueTooBigError):
            i=12
            min_range = 0
            max_range = 11
            is_integer(i, min_range, max_range)

    def test_should_raise_exception_for_integer_below_range(self):
        with self.assertRaises(VdtValueTooSmallError):
            i=1
            min_range = 2
            max_range = 11
            is_integer(i, min_range, max_range)

    def test_should_validate_string(self):
        string = "Hello"
        is_valid = is_string(string)
        self.assertTrue(is_valid)


    def test_should_validate_range(self):
        some_text = "something"
        min_range = 0
        max_range = 11
        isvalid = is_string(some_text, min_range, max_range)
        self.assertTrue(isvalid)

    def test_should_raise_exception_for_integer_above_range(self):
        with self.assertRaises(VdtValueTooLongError):
            some_text = "something wrong"
            min_range = 0
            max_range = 11
            is_string(some_text, min_range, max_range)

    def test_should_raise_exception_for_integer_below_range(self):
        with self.assertRaises(VdtValueTooShortError):
            some_text = "wrong"
            min_range = 11
            max_range = 23
            is_string(some_text, min_range, max_range)

    def test_should_select_one_option(self):
        list=["asif","mahesh"]
        self.assertTrue(is_option_in_list("asif",list))

