from unittest import TestCase
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mock import Mock, patch
from mangrove.errors.MangroveException import DataObjectNotFound
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.validator_factory import validator_factory
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.field import HierarchyField, TextField
from mangrove.contrib.delete_validators import EntityShouldExistValidator
from collections import OrderedDict


class TestEntityShouldExistValidator(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.get_by_short_code_patcher = patch('mangrove.contrib.delete_validators.get_by_short_code')
        self.get_by_short_code_mock = self.get_by_short_code_patcher.start()

        self.validator = EntityShouldExistValidator()
        self.field1 = HierarchyField('a', 'entity_type', 'a', Mock(spec=DataDictType))
        self.field2 = TextField('b', 'entity_id', 'b', Mock(spec=DataDictType), entity_question_flag=True)
        self.field1.set_value('clinic')
        self.field2.set_value('cli01')
        self.fields = [self.field1, self.field2]

        self.entity_type = 'clinic'
        self.entity_id = 'cli01'
        self.values={
            'entity_type': self.entity_type,
            'entity_id': self.entity_id
        }

    def tearDown(self):
        self.get_by_short_code_patcher.stop()


    def test_should_give_error_if_entity_does_not_exist(self):
        self.get_by_short_code_mock.side_effect = DataObjectNotFound('Entity', "Unique Identification Number (ID)", self.entity_id)
        exception = DataObjectNotFound("Entity", "Unique Identification Number (ID)", self.entity_id)
        errors = OrderedDict()
        errors['entity_type'] = exception.message
        errors['entity_id'] = exception.message
        self.assertEqual(errors, self.validator.validate(self.values, self.fields, self.dbm))
        self.get_by_short_code_mock.assert_called_once_with(self.dbm, self.entity_id, [self.entity_type])

    def test_should_not_give_error_if_entity_exist(self):
        self.assertEqual(OrderedDict(), self.validator.validate(self.values, self.fields, self.dbm))
        self.get_by_short_code_mock.assert_called_once_with(self.dbm, self.entity_id, [self.entity_type])

    def test_should_create_entity_should_exist_validator_from_json(self):
        validator_json = {
            'cls': ValidatorTypes.ENTITY_SHOULD_EXIST
        }
        self.assertTrue(isinstance(validator_factory(validator_json), EntityShouldExistValidator))

    def test_entity_should_exist_validators_should_be_serializable(self):
        expected_json = {
            'cls': ValidatorTypes.ENTITY_SHOULD_EXIST
        }
        self.assertEqual(expected_json, self.validator.to_json())
