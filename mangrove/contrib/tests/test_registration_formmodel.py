
import unittest
from mangrove.form_model.form_model import REGISTRATION_FORM_CODE, MOBILE_NUMBER_FIELD_CODE
from mangrove.contrib.registration import GLOBAL_REGISTRATION_FORM_CODE
from mangrove.utils.test_utils.database_utils import create_dbmanager_for_ut, delete_and_create_form_model
from mangrove.datastore.database import  _delete_db_and_remove_db_manager
from mangrove.datastore.cache_manager import get_cache_manager


class TestRegistrationFormModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_dbmanager_for_ut(cls)
        cls.form = delete_and_create_form_model(cls.manager, GLOBAL_REGISTRATION_FORM_CODE)

    @classmethod
    def tearDownClass(cls):
        _delete_db_and_remove_db_manager(cls.manager)
        get_cache_manager().flush_all()

    def test_should_create_registration_form_model(self):
        self.assertEqual(7, len(self.form.fields))
        self.assertEqual(REGISTRATION_FORM_CODE, self.form.form_code)

    def test_registration_form_should_have_entity_type_field(self):
        self.assertIsNotNone(self.form._get_field_by_code("T"))

    def test_registration_form_should_have_multiple_constraints_on_mobile(self):
        field = self.form._get_field_by_code(MOBILE_NUMBER_FIELD_CODE)
        self.assertEqual(15, field.constraints[0].max)
        self.assertEqual("^[0-9]+$", field.constraints[1].pattern)

    def test_form_submission_should_be_invalid_if_no_location_field_provided_while_registering_an_entity(self):
        answers = {"s": "1", "t": "Reporter", "m": "1212121212"}
        cleaned_data, errors = self.form.validate_submission(answers)
        self.assertTrue('g' in errors)

if __name__ == '__main__':
    unittest.main()
