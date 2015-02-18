from collections import OrderedDict
import unittest
from mangrove.datastore.documents import EntityDocument
from mock import Mock, patch, MagicMock
from mangrove.form_model.form_model import GLOBAL_REGISTRATION_FORM_ENTITY_TYPE
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity, Contact
from mangrove.form_model.field import TextField, DateField, UniqueIdField, ShortCodeField
from mangrove.form_model.form_model import FormModel
from mangrove.form_model.form_submission import FormSubmissionFactory

ENTITY_TYPE = ["Clinic"]


class TestFormSubmission(unittest.TestCase):
    def _create_data_submission_form(self):
        question1 = UniqueIdField('clinic',name="entity_question", code="ID", label="What is associated entity")
        question2 = TextField(name="Name", code="Q1", label="What is your name",
                              defaultValue="some default value")
        return FormModel(self.dbm, name="aids", label="Aids form_model",
                         form_code="AIDS",
                         fields=[question1, question2])

    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        view_mock = Mock()
        view_mock.data_record_by_form_code.return_value = []
        view_mock.by_short_codes.return_value = None
        self.dbm.view = view_mock

    def test_should_create_form_submission_with_entity_id(self):
        form_model = self._create_data_submission_form()
        answers = OrderedDict({"id": "1", "q1": "My Name"})

        form_submission = FormSubmissionFactory().get_form_submission(form_model, answers)

        self.assertEqual(form_submission.form_code, "AIDS")
        self.assertEqual(form_submission.short_code, "1")
        self.assertEqual(form_submission.entity_type, [each.lower() for each in ENTITY_TYPE])


    def test_should_create_global_form_submission_location_tree(self):
        form_model = self._construct_global_registration_form()
        submission = OrderedDict({"s": "1", "t": "Reporter", "l": "pune", "m": "1212121212"})
        with patch('mangrove.form_model.form_submission.GlobalRegistrationFormSubmission.create_entity') as create_entity:
            entity_mock = Mock(spec=Contact)
            entity_mock.add_data.return_value = 1
            create_entity.return_value = entity_mock

            location_tree = {1: 2}
            form_submission = FormSubmissionFactory().get_form_submission(form_model, submission,
                                                                          location_tree=location_tree)
            data_record_id = form_submission.save(self.dbm)
            self.assertEqual(1, data_record_id)
            self.assertEqual(form_submission.location_tree, location_tree)

    def _assert_data_submission_entity_mock(self, entity_mock, event_time=None):
        submission_values = [('Name', 'My Name')]
        if event_time is not None:
            submission_values.append(("Event time", event_time))
        submission_values.append(('entity_question', '1'))

        submission_information = {'form_code': u'AIDS'}
        entity_mock.add_data.assert_called_once_with(data=submission_values,
                                                     event_time=event_time, submission=submission_information)

    def _construct_global_registration_form(self):
        mocked_form_model = Mock()
        mocked_form_model.entity_type = GLOBAL_REGISTRATION_FORM_ENTITY_TYPE
        mocked_form_model.entity_questions = [ShortCodeField('name','s','label')]

        return mocked_form_model
