# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mock import Mock
from mangrove.datastore.database import DatabaseManager, View
from mangrove.errors.error_codes import EMAIL_NOT_UNIQUE, INVALID_EMAIL, ATLEAST_SINGLE_LOCATION_ENTRY_SHOULD_BE_PRESENT, DUPLICATE_MOBILE_NUMBER, EMPTY_MOBILE_NUMBER
from mangrove.form_model.tests.test_form_model_unit_tests import DatabaseManagerStub
from mangrove.form_model.validator_factory import validator_factory
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.form_model.field import HierarchyField, GeoCodeField, TextField, Field
from mangrove.form_model.form_model import LOCATION_TYPE_FIELD_NAME, LOCATION_TYPE_FIELD_CODE, GEO_CODE_FIELD_NAME, GEO_CODE, EMAIL_FIELD
from mangrove.contrib.registration_validators import AtLeastOneLocationFieldMustBeAnsweredValidator, MobileNumberValidationsForReporter, EmailFieldValidatorForReporter
from mangrove.datastore.datadict import DataDictType


class TestAtLeastOneLocationFieldMustBeAnsweredValidator(unittest.TestCase):
    def setUp(self):
        self.validator = AtLeastOneLocationFieldMustBeAnsweredValidator()
        self.field1 = HierarchyField(name=LOCATION_TYPE_FIELD_NAME, code=LOCATION_TYPE_FIELD_CODE,
                                     label="What is the subject's location?", ddtype=Mock(spec=DataDictType),
                                     instruction="Enter a region, district, or commune",
                                     required=False)
        self.field2 = GeoCodeField(name=GEO_CODE_FIELD_NAME, code=GEO_CODE,
                                   label="What is the subject's GPS co-ordinates?",
                                   ddtype=Mock(spec=DataDictType), instruction="Enter lat and long. Eg 20.6, 47.3",
                                   required=False)
        self.field3 = TextField('a', 'a', 'a', Mock(spec=DataDictType))
        self.field4 = TextField('b', 'b', 'b', Mock(spec=DataDictType))

        self.fields = [self.field1, self.field2, self.field3, self.field4]

    def test_should_return_error_dict_if_mobile_number_field_missing(self):
        values = dict(a='test2', b='reporter')
        error_dict = self.validator.validate(values, self.fields)
        self.assertEqual(2, len(error_dict))
        self.assertEqual(error_dict[0].code, ATLEAST_SINGLE_LOCATION_ENTRY_SHOULD_BE_PRESENT)
        self.assertEqual(error_dict[1].code, ATLEAST_SINGLE_LOCATION_ENTRY_SHOULD_BE_PRESENT)

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


class TestMobileNumberValidatorForReporter(unittest.TestCase):
    def setUp(self):
        self.validator = MobileNumberValidationsForReporter()
        self.field1 = TextField('t', 't', 't', Mock(spec=DataDictType), entity_question_flag=True)
        self.field2 = TextField('m', 'm', 'm', Mock(spec=DataDictType))
        self.fields = [self.field1, self.field2]
        self.dbm = Mock(spec=DatabaseManager)
        self.dbm.view = Mock()
        self.dbm.view.datasender_by_mobile = Mock(return_value=[{'doc': {
            "data": {"mobile_number": {"value": "123"}},
            "short_code": "abc"
        }}])


    def test_should_return_error_dict_if_mobile_number_field_missing(self):
        values = dict(t='reporter')
        error_list = self.validator.validate(values, self.fields, self.dbm)
        self.assertEqual(1, len(error_list))
        self.assertEqual(EMPTY_MOBILE_NUMBER, error_list[0].code)

    def test_should_return_error_dict_if_mobile_number_allready_exist(self):
        entity_mock = Mock()
        entity_mock.value.return_value = '123'
        values = dict(t='reporter', m='123')
        error_list = self.validator.validate(values, self.fields, self.dbm)
        self.assertEqual(1, len(error_list))
        self.assertEqual(error_list[0].code, DUPLICATE_MOBILE_NUMBER)

    def test_should_create_mobile_number_mandatory_for_reporter_validator_from_json(self):
        validator_json = {
            'cls': ValidatorTypes.MOBILE_NUMBER_MANDATORY_FOR_REPORTER
        }

        self.assertTrue(
            isinstance(validator_factory(validator_json), MobileNumberValidationsForReporter))

    def test_mobile_number_mandatory_for_reporter_validator_should_be_serializable(self):
        expected_json = {
            'cls': ValidatorTypes.MOBILE_NUMBER_MANDATORY_FOR_REPORTER
        }
        self.assertEqual(expected_json, self.validator.to_json())

    def test_should_return_error_if_duplicate_mobile_number_comes_in_epsilon_format_from_excel_file(self):
        entity_mock = Mock()
        entity_mock.value.return_value = '266123321435'
        values = dict(t='reporter', m='2.66123321435e+11')
        error_list = self.validator.validate(values, self.fields, self.dbm)
        self.assertEqual(1, len(error_list))
        self.assertEqual('m', error_list[0].field_name)
        self.assertEqual(DUPLICATE_MOBILE_NUMBER,error_list[0].code)

    def test_should_return_error_if_mobile_number_has_hyphens_from_excel_file(self):
        entity_mock = Mock()
        entity_mock.value.return_value = '266123321435'
        values = dict(t='reporter', m='266-123321435')
        error_list = self.validator.validate(values, self.fields, self.dbm)
        self.assertEqual(1, len(error_list))
        self.assertEqual('m', error_list[0].field_name)
        self.assertEqual(DUPLICATE_MOBILE_NUMBER,error_list[0].code)

    def test_should_return_error_if_mobile_number_comes_as_floating_point_number_from_excel_file(self):
        entity_mock = Mock()
        entity_mock.value.return_value = '266123321435'
        values = dict(t='reporter', m='266123321435.0')
        error_list = self.validator.validate(values, self.fields, self.dbm)
        self.assertEqual(1, len(error_list))
        self.assertEqual('m', error_list[0].field_name)
        self.assertEqual(DUPLICATE_MOBILE_NUMBER,error_list[0].code)


class TestEmailValidator(unittest.TestCase):

    def test_should_not_return_error_when_email_field_is_not_present(self):
        email_validator = EmailFieldValidatorForReporter()
        errors = email_validator.validate({'name': 'cf'}, [Field(name='email', code='email',ddtype=Mock(spec=DataDictType))], Mock(spec=DatabaseManager))
        self.assertEqual(len(errors), 0)

    def test_should_not_return_error_for_invalid_email(self):
        email_validator = EmailFieldValidatorForReporter()
        errors = email_validator.validate({'email': 'cf'}, [Field(name='email', code='email',ddtype=Mock(spec=DataDictType))], Mock(spec=DatabaseManager))
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, INVALID_EMAIL)

    def test_should_return_error_for_duplicate_email(self):
        email_validator = EmailFieldValidatorForReporter()
        manager_stub = DatabaseManagerStub()
        manager_stub.view.datasender_by_email.return_value = ["a@a.com"]

        errors = email_validator.validate({'email': 'a@a.com'}, [Field(name='email', code='email',ddtype=Mock(spec=DataDictType))],
                                          manager_stub)

        self.assertEqual(errors[0].code, EMAIL_NOT_UNIQUE)

