
from collections import OrderedDict
from unittest import TestCase
from mock import Mock, patch
from mangrove.form_model.form_model import FormModel
from mangrove.form_model.form_submission import FormSubmissionFactory
from mangrove.datastore.database import DatabaseManager
from mangrove.transport.player.handler import UpdateEntityHandler

class TestEditRegistrationHandler(TestCase):
    def setUp(self):
        self.dbm = Mock(spec = DatabaseManager)
        self.handler = UpdateEntityHandler(self.dbm)
        self.form_submission_mock = Mock()
        self.form_model_mock = Mock(spec=FormModel)
        self.reporter_names = Mock()
        self.location_tree = Mock()


    def tearDown(self):
        pass

    def test_should_handle_valid_request(self):
        self.form_submission_mock.is_valid = True
        with patch.object(FormSubmissionFactory, 'get_form_submission') as get_form_submission_mock:
            get_form_submission_mock.return_value = self.form_submission_mock
            response = self.handler.handle(self.form_model_mock, OrderedDict(), OrderedDict(),
                self.reporter_names, self.location_tree)
            self.assertTrue(response.success)
            self.assertEqual(1, self.form_submission_mock.update.call_count)
            self.assertEqual(self.reporter_names, response.reporters)


    def test_should_handle_invalid_request(self):
        self.form_submission_mock.is_valid = False
        self.form_submission_mock.saved = False
        with patch.object(FormSubmissionFactory, 'get_form_submission') as get_form_submission_mock:
            get_form_submission_mock.return_value = self.form_submission_mock
            response = self.handler.handle(self.form_model_mock, OrderedDict(), OrderedDict(),
                self.reporter_names, self.location_tree)
            self.assertFalse(response.success)
            self.assertEqual(0, self.form_submission_mock.save.call_count)

