# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.contrib.delete_validators import EntityShouldExistValidator
from mangrove.form_model.validators import MandatoryValidator
from mangrove.form_model.form_model import ENTITY_TYPE_FIELD_CODE, SHORT_CODE, get_form_model_by_code
from mangrove.contrib.deletion import create_default_delete_form_model, ENTITY_DELETION_FORM_CODE
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestEntityDeletionFormModel(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)
        self.form_model = create_default_delete_form_model(self.manager)

    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def test_should_create_deletion_form_model(self):
        form = get_form_model_by_code(self.manager, ENTITY_DELETION_FORM_CODE)
        self.assertEqual(2, len(form.fields))

    def test_delete_form_should_have_entity_type_field(self):
        self.assertIsNotNone(self.form_model._get_field_by_code(ENTITY_TYPE_FIELD_CODE))

    def test_delete_form_model_should_have_all_required_validators(self):
        delete_form = get_form_model_by_code(self.manager, ENTITY_DELETION_FORM_CODE)
        self.assertEqual(2, len(delete_form.validators))
        self.assertIsInstance(delete_form.validators[0], MandatoryValidator)
        self.assertIsInstance(delete_form.validators[1], EntityShouldExistValidator)

    def test_form_submission_should_be_invalid_if_entity_does_not_exist_while_deleting_an_entity(self):
        answers = {SHORT_CODE: "1", ENTITY_TYPE_FIELD_CODE: "Reporter"}
        delete_form = get_form_model_by_code(self.manager, ENTITY_DELETION_FORM_CODE)
        delete_form.bind(answers)
        cleaned_data, errors = delete_form.validate_submission(answers)
        self.assertTrue(SHORT_CODE in errors)
        self.assertTrue(ENTITY_TYPE_FIELD_CODE in errors)




