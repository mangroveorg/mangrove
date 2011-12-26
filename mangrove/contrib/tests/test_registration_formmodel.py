from mangrove.forms.forms import form_by_code
from mangrove.form_model.form_model import REGISTRATION_FORM_CODE, MOBILE_NUMBER_FIELD_CODE
from mangrove.contrib.registration_form import create_default_registration_form
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestRegistrationFormModel(MangroveTestCase):

    def setUp(self):
        MangroveTestCase.setUp(self)

    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def test_should_create_registration_form_model(self):
        form = create_default_registration_form(self.manager)
        self.assertEqual(7, len(form.fields))
        self.assertEqual(REGISTRATION_FORM_CODE, form.code)

    def test_registration_form_should_have_entity_type_field(self):
        form = create_default_registration_form(self.manager)
        self.assertIsNotNone(form["t"])

    def test_registration_form_should_have_multiple_constraints_on_mobile(self):
        form = create_default_registration_form(self.manager)
        field = form[MOBILE_NUMBER_FIELD_CODE]
        self.assertEqual(15, field.validators[0].max)
        self.assertEqual("^[0-9]+$", field.validators[1].pattern)

    def test_registration_form_validate_submission(self):
        create_default_registration_form(self.manager)
        Form = form_by_code(self.manager, "reg")
        self.assertTrue(Form(data={"s": "1", "t": ["Reporter"], "g": "1 1", "m": "1212121212", "n":"foo"}).is_valid())
        
    def test_registration_form_invalid_submission(self):
        create_default_registration_form(self.manager)
        Form = form_by_code(self.manager, "reg")
        form = Form(data={"s": "1", "t": "Reporter", "g": "1 1", "m": "1212121212"})
        self.assertFalse(form.is_valid())
        self.assertEqual(2, len(form.errors))
        self.assertEqual(['This field is required.'], form.errors['n'])
        self.assertEqual(['The value should be a sequence'], form.errors['t'])

#    def test_should_throw_exception_if_no_location_field_provided_while_registering_an_entity(self):
#        answers = {"s": "1", "t": "Reporter", "m": "1212121212"}
#        registration_form = _construct_registration_form(self.manager)
#        with self.assertRaises(LocationFieldNotPresentException):
#            registration_form.validate_submission(answers)
