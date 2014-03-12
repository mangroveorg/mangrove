import unittest
from mock import Mock, patch, MagicMock
from mangrove.datastore.database import DatabaseManager
from mangrove.errors.MangroveException import DataObjectNotFound
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.form_model.validator_factory import validator_factory
from mangrove.form_model.field import TextField, UniqueIdField
from mangrove.form_model.validators import MandatoryValidator, UniqueIdExistsValidator
from mangrove.datastore.entity import Entity


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


class TestUniqueIdExistsValidator(unittest.TestCase):
    def setUp(self):
        self.validator = UniqueIdExistsValidator()
        self.field1 = TextField('a', 'a', 'a')
        self.field2 = TextField('b', 'b', 'b')
        self.field3 = UniqueIdField('unique_id_type1', 'name1', 'code1', 'label1')
        self.field4 = UniqueIdField('unique_id_type2', 'name2', 'code2', 'label2')
        self.fields = [self.field1, self.field2, self.field3,
                       self.field4
        ]


    def test_should_not_return_error_if_unique_id_exists(self):
        values = dict(a='text1', b='text2', code1='unique_id1', code2='unique_id2')
        dbm = Mock(spec=DatabaseManager)
        with patch('mangrove.form_model.validators.get_by_short_code') as get_by_short_code:
            get_by_short_code.return_value = Mock(spec=Entity)
            errors = self.validator.validate(values, self.fields, dbm)
            self.assertEquals(0, len(errors))

    def test_should_return_error_if_unique_id_does_not_exist(self):
        values = dict(a='text1', b='text2', code1='invalid_id', code2='valid_code')
        dbm = Mock(spec=DatabaseManager)
        with patch('mangrove.form_model.validators.get_by_short_code') as get_by_short_code:
            get_by_short_code.side_effect = [DataObjectNotFound('Entity','short_code','invalid_id'),Mock(spec=Entity)]
            errors = self.validator.validate(values, self.fields, dbm)
            self.assertEquals(1, len(errors))
            self.assertEquals(errors['code1'],u'Entity with short_code = invalid_id not found.')


