# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mock import Mock, patch
from datastore.database import DatabaseManager
from mangrove.form_model.validator_factory import validator_factory
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.form_model.field import HierarchyField, GeoCodeField, TextField
from mangrove.form_model.form_model import LOCATION_TYPE_FIELD_NAME, LOCATION_TYPE_FIELD_CODE, GEO_CODE_FIELD, GEO_CODE, REPORTER, MOBILE_NUMBER_FIELD
from mangrove.contrib.registration_validators import AtLeastOneLocationFieldMustBeAnsweredValidator, MobileNumberValidationsForReporterRegistrationValidator
from mangrove.datastore.datadict import DataDictType

class TestAtLeastOneLocationFieldMustBeAnsweredValidator(unittest.TestCase):
    def setUp(self):
        self.validator = AtLeastOneLocationFieldMustBeAnsweredValidator()
        self.field1 = HierarchyField(name=LOCATION_TYPE_FIELD_NAME, code=LOCATION_TYPE_FIELD_CODE,
            label="What is the subject's location?",
            language="en", ddtype=Mock(spec=DataDictType), instruction="Enter a region, district, or commune",
            required=False)
        self.field2 = GeoCodeField(name=GEO_CODE_FIELD, code=GEO_CODE, label="What is the subject's GPS co-ordinates?",
            language="en", ddtype=Mock(spec=DataDictType), instruction="Enter lat and long. Eg 20.6, 47.3",
            required=False)
        self.field3 = TextField('a', 'a', 'a', Mock(spec=DataDictType))
        self.field4 = TextField('b', 'b', 'b', Mock(spec=DataDictType))

        self.fields = [self.field1, self.field2, self.field3, self.field4]

    def test_should_return_error_dict_if_mobile_number_field_missing(self):
        values = dict(a='test2', b='reporter')
        error_dict = self.validator.validate(values, self.fields)
        self.assertEqual(2, len(error_dict))
        self.assertTrue(LOCATION_TYPE_FIELD_CODE in error_dict)
        self.assertTrue(GEO_CODE in error_dict)

    def test_should_create_mobile_number_mandatory_for_reporter_validator_from_json(self):
        validator_json = {
            'cls': ValidatorTypes.At_Least_One_Location_Field_Must_Be_Answered
        }

        self.assertTrue(isinstance(validator_factory(validator_json), AtLeastOneLocationFieldMustBeAnsweredValidator))

    def test_mobile_number_mandatory_for_reporter_validator_should_be_serializable(self):
        expected_json = {
            'cls': ValidatorTypes.At_Least_One_Location_Field_Must_Be_Answered
        }
        self.assertEqual(expected_json, self.validator.to_json())


class TestMobileNumberMandatoryValidationsForReporterRegistrationValidator(unittest.TestCase):
    def setUp(self):
        self.validator = MobileNumberValidationsForReporterRegistrationValidator()
        self.field1 = TextField('t', 't', 't', Mock(spec=DataDictType), entity_question_flag=True)
        self.field2 = TextField('m', 'm', 'm', Mock(spec=DataDictType))
        self.fields = [self.field1, self.field2]
        self.dbm = Mock(spec=DatabaseManager)

    def test_should_return_error_dict_if_mobile_number_field_missing(self):
        values = dict(t='reporter')
        error_dict = self.validator.validate(values, self.fields, self.dbm)
        self.assertEqual(1, len(error_dict))
        self.assertTrue('m' in error_dict.keys())

    def test_should_return_error_dict_if_mobile_number_allready_exist(self):
        patcher = patch('mangrove.contrib.registration_validators.entities_exists_with_value')
        entity_exists_mock = patcher.start()
        entity_exists_mock.return_value = True
        values = dict(t='reporter', m='123')
        error_dict = self.validator.validate(values, self.fields, self.dbm)
        self.assertEqual(1, len(error_dict))
        self.assertTrue('m' in error_dict.keys())
        entity_exists_mock.assert_called_once_with(self.dbm, [REPORTER], MOBILE_NUMBER_FIELD, '123')
        patcher.stop()

    def test_should_create_mobile_number_mandatory_for_reporter_validator_from_json(self):
        validator_json = {
            'cls': ValidatorTypes.MOBILE_NUMBER_MANDATORY_FOR_REPORTER
        }

        self.assertTrue(isinstance(validator_factory(validator_json), MobileNumberValidationsForReporterRegistrationValidator))

    def test_mobile_number_mandatory_for_reporter_validator_should_be_serializable(self):
        expected_json = {
            'cls': ValidatorTypes.MOBILE_NUMBER_MANDATORY_FOR_REPORTER
        }
        self.assertEqual(expected_json, self.validator.to_json())
