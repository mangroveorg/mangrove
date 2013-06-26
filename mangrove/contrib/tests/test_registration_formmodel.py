# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.errors.MangroveException import DataObjectAlreadyExists, FormModelDoesNotExistsException
from mangrove.form_model.form_model import REGISTRATION_FORM_CODE, MOBILE_NUMBER_FIELD_CODE, get_form_model_by_code
from mangrove.contrib.registration import create_default_reg_form_model, GLOBAL_REGISTRATION_FORM_CODE
from mangrove.utils.test_utils.database_utils import create_dbmanager_for_ut, delete_and_create_form_model
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestRegistrationFormModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_dbmanager_for_ut(cls)
        cls.form = delete_and_create_form_model(cls.manager, GLOBAL_REGISTRATION_FORM_CODE)


    def test_should_create_registration_form_model(self):
        self.assertEqual(6, len(self.form.fields))
        self.assertEqual(REGISTRATION_FORM_CODE, self.form.form_code)
        self.assertEqual('string', self.form.fields[3].ddtype.primitive_type)

    def test_registration_form_should_have_entity_type_field(self):
        self.assertIsNotNone(self.form._get_field_by_code("T"))

    def test_registration_form_should_have_multiple_constraints_on_mobile(self):
        field = self.form._get_field_by_code(MOBILE_NUMBER_FIELD_CODE)
        self.assertEqual(15, field.constraints[0].max)
        self.assertEqual("^[0-9]+$", field.constraints[1].pattern)

    def test_form_submission_should_be_invalid_if_no_location_field_provided_while_registering_an_entity(self):
        answers = {"s": "1", "t": "Reporter", "m": "1212121212"}
        cleaned_data, errors = self.form.validate_submission(answers)
        self.assertTrue('l' in errors)
        self.assertTrue('g' in errors)

if __name__ == '__main__':
    unittest.main()
