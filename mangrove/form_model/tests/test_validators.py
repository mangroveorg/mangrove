
import unittest
from mock import Mock
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.form_model.validator_factory import validator_factory
from mangrove.form_model.field import TextField
from mangrove.form_model.validators import MandatoryValidator

class TestMandatoryValidator(unittest.TestCase):
    def setUp(self):
        self.validator = MandatoryValidator()
        self.field1 = TextField('a', 'a', 'a')
        self.field2 = TextField('b', 'b', 'b', required=False)
        self.field3 = TextField('c', 'c', 'c')
        self.field4 = TextField('d', 'd', 'd')
        self.fields = [self.field1, self.field2, self.field3, self.field4]

    def tearDown(self):
        pass

    def test_should_find_mandatory_fields(self):
        mandatory_field_list = self.validator.get_mandatory_fields(self.fields)
        self.assertEqual(3, len(mandatory_field_list))

    def test_should_return_error_dict_if_mandatory_field_answer_not_present(self):
        values = dict(a='test1', b='test2', d='test4')
        errors = self.validator.validate(values, self.fields)
        self.assertEqual(1, len(errors.keys()))
        self.assertTrue('c' in errors.keys())
        self.assertFalse('a' in errors.keys())

    def test_should_create_mandatory_validator_from_json(self):
        validator_json = {
            'cls': ValidatorTypes.MANDATORY
        }
        self.assertTrue(isinstance(validator_factory(validator_json), MandatoryValidator))

    def test_mandatory_validators_should_be_serializable(self):
        expected_json = {
            'cls': ValidatorTypes.MANDATORY
        }
        self.assertEqual(expected_json, self.validator.to_json())


