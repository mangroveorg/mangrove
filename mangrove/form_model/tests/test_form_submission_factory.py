from collections import OrderedDict
import unittest
from mock import Mock
from mangrove.form_model.form_model import EntityRegistrationFormSubmission
from mangrove.form_model.form_model import GlobalRegistrationFormSubmission, GLOBAL_REGISTRATION_FORM_ENTITY_TYPE
from mangrove.form_model.form_model import DataFormSubmission, FormSubmissionFactory, FormModel

class TestFormSubmissionFactory(unittest.TestCase):
    def test_should_give_data_form_submission(self):
        mocked_form_model = Mock(spec=FormModel)
        mocked_form_model.is_registration_form.return_value = False
        mocked_form_model.entity_type = "clinic"
        form_submission = FormSubmissionFactory().get_form_submission(mocked_form_model,OrderedDict(),None)
        self.assertEqual(type(form_submission), DataFormSubmission)

    def test_should_give_global_registration_form_submission(self):
        mocked_form_model = Mock(spec=FormModel)
        mocked_form_model.is_registration_form.return_value = True
        mocked_form_model.entity_type= GLOBAL_REGISTRATION_FORM_ENTITY_TYPE
        form_submission = FormSubmissionFactory().get_form_submission(mocked_form_model,OrderedDict(),None)
        self.assertEqual(type(form_submission), GlobalRegistrationFormSubmission)

    def test_should_give_entity_specific_registration_form_submission(self):
        mocked_form_model = Mock(spec=FormModel)
        mocked_form_model.is_registration_form.return_value = True
        mocked_form_model.entity_type= "clinic"
        form_submission = FormSubmissionFactory().get_form_submission(mocked_form_model,OrderedDict(),None)
        self.assertEqual(type(form_submission), EntityRegistrationFormSubmission)
