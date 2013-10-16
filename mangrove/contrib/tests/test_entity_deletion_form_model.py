
import unittest
from mangrove.contrib.delete_validators import EntityShouldExistValidator
from mangrove.errors.MangroveException import DataObjectAlreadyExists, FormModelDoesNotExistsException
from mangrove.form_model.validators import MandatoryValidator
from mangrove.form_model.form_model import ENTITY_TYPE_FIELD_CODE, SHORT_CODE, get_form_model_by_code
from mangrove.contrib.deletion import create_default_delete_form_model, ENTITY_DELETION_FORM_CODE
from mangrove.utils.test_utils.database_utils import create_dbmanager_for_ut, delete_and_create_form_model


class TestEntityDeletionFormModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        create_dbmanager_for_ut(cls)
        cls.form = delete_and_create_form_model(cls.manager, ENTITY_DELETION_FORM_CODE)

    def test_should_create_deletion_form_model(self):
        self.assertEqual(2, len(self.form.fields))

    def test_delete_form_should_have_entity_type_field(self):
        self.assertIsNotNone(self.form._get_field_by_code(ENTITY_TYPE_FIELD_CODE))

    def test_delete_form_model_should_have_all_required_validators(self):
        self.assertEqual(2, len(self.form.validators))
        self.assertIsInstance(self.form.validators[0], MandatoryValidator)
        self.assertIsInstance(self.form.validators[1], EntityShouldExistValidator)

    def test_form_submission_should_be_invalid_if_entity_does_not_exist_while_deleting_an_entity(self):
        answers = {SHORT_CODE: "1", ENTITY_TYPE_FIELD_CODE: "Reporter"}
        self.form.bind(answers)
        cleaned_data, errors = self.form.validate_submission(answers)
        self.assertTrue(SHORT_CODE in errors)
        self.assertTrue(ENTITY_TYPE_FIELD_CODE in errors)


if __name__ == '__main__':
    unittest.main()