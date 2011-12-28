# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.form_model.form_model import REGISTRATION_FORM_CODE, MOBILE_NUMBER_FIELD_CODE
from mangrove.contrib.registration import _construct_registration_form, create_default_reg_form_model
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestRegistrationFormModel(MangroveTestCase):

    def setUp(self):
        MangroveTestCase.setUp(self)

    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def test_should_create_registration_form_model(self):
        form = create_default_reg_form_model(self.manager)
        self.assertEqual(7, len(form.fields))
        self.assertEqual(REGISTRATION_FORM_CODE, form.form_code)
        self.assertEqual('string', form.fields[3].ddtype.primitive_type)

    def test_should_create_registration_form_mode(self):
        form = _construct_registration_form(self.manager)
        self.assertEqual(7, len(form.fields))
        self.assertEqual(REGISTRATION_FORM_CODE, form.form_code)

    def test_registration_form_should_have_entity_type_field(self):
        form = _construct_registration_form(self.manager)
        self.assertIsNotNone(form.get_field_by_code("T"))

    def test_registration_form_should_have_multiple_constraints_on_mobile(self):
        form = _construct_registration_form(self.manager)
        field = form.get_field_by_code(MOBILE_NUMBER_FIELD_CODE)
        self.assertEqual(15, field.constraints[0].max)
        self.assertEqual("^[0-9]+$", field.constraints[1].pattern)

    def test_create_form_submission_with_entity_type_as_lowercase_list_of_string(self):
        answers = {"s": "1", "t": "Reporter", "g": "1 1", "m": "1212121212"}
        registration_form = _construct_registration_form(self.manager)
        form_submission = registration_form.validate_submission(answers)
        self.assertEqual(["reporter"], form_submission.entity_type)


    def test_form_submission_should_be_invalid_if_no_location_field_provided_while_registering_an_entity(self):
        answers = {"s": "1", "t": "Reporter", "m": "1212121212"}
        registration_form = _construct_registration_form(self.manager)
        form_submission = registration_form.validate_submission(answers)
        self.assertFalse(form_submission.is_valid)
        self.assertTrue('l' in form_submission.errors)
        self.assertTrue('g' in form_submission.errors)