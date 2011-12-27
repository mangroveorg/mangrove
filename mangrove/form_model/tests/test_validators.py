# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mock import Mock
from mangrove.form_model.validators import ValidatorTypes, validator_factory
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.field import TextField
from mangrove.form_model.validators import MandatoryValidator, MobileNumberMandatoryForReporterRegistrationValidator

class TestMandatoryValidator(unittest.TestCase):
    def setUp(self):
        self.validator = MandatoryValidator()
        self.field1 = TextField('a', 'a', 'a', Mock(spec=DataDictType))
        self.field2 = TextField('b', 'b', 'b', Mock(spec=DataDictType), required=False)
        self.field3 = TextField('c', 'c', 'c', Mock(spec=DataDictType))
        self.field4 = TextField('d', 'd', 'd', Mock(spec=DataDictType))
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


class TestMobileNumberMandatoryForReporterRegistrationValidator(unittest.TestCase):
    def setUp(self):
        self.validator = MobileNumberMandatoryForReporterRegistrationValidator()
        self.field1 = TextField('t', 't', 't', Mock(spec=DataDictType), entity_question_flag=True)
        self.field2 = TextField('m', 'm', 'm', Mock(spec=DataDictType))
        self.fields = [self.field1, self.field2]

    def test_should_return_error_dict_if_mobile_number_field_missing(self):
        values = dict(b='test2', t='reporter')
        error_dict = self.validator.validate(values, self.fields)
        self.assertEqual(1, len(error_dict))
        self.assertTrue('m' in error_dict.keys())

    def test_should_create_mobile_number_mandatory_for_reporter_validator_from_json(self):
        validator_json = {
            'cls': ValidatorTypes.MOBILE_NUMBER_MANDATORY_FOR_REPORTER
        }

        self.assertTrue(isinstance(validator_factory(validator_json), MobileNumberMandatoryForReporterRegistrationValidator))

    def test_mobile_number_mandatory_for_reporter_validator_should_be_serializable(self):
        expected_json = {
            'cls': ValidatorTypes.MOBILE_NUMBER_MANDATORY_FOR_REPORTER
        }
        self.assertEqual(expected_json, self.validator.to_json())
