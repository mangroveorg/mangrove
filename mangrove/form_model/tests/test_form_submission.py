# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from collections import OrderedDict
import datetime
import unittest
from mock import Mock, patch
from mangrove.form_model.form_model import GLOBAL_REGISTRATION_FORM_ENTITY_TYPE
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType
from mangrove.datastore.entity import Entity
from mangrove.form_model.field import TextField, DateField
from mangrove.form_model.form_model import FormModel, FormSubmissionFactory


class TestFormSubmission(unittest.TestCase):
    def _create_data_submission_form(self):
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
            language="eng", entity_question_flag=True, ddtype=self.ddtype_mock)
        question2 = TextField(name="Name", code="Q1", label="What is your name",
            defaultValue="some default value", language="eng", ddtype=self.ddtype_mock)
        event_time_field_code = "ET"
        self.event_time_question = DateField(name="Event time", code=event_time_field_code,
            label="Event time field",
            date_format="dd.mm.yyyy", ddtype=self.ddtype_mock, required=False, event_time_field_flag=True)
        return FormModel(self.dbm, entity_type=["Clinic"], name="aids", label="Aids form_model",
            form_code="AIDS", type='survey',
            fields=[question1, question2, self.event_time_question])

    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.ddtype_mock = Mock(spec=DataDictType)
        view_mock = Mock()
        view_mock.data_record_by_form_code.return_value = []
        view_mock.by_short_codes.return_value = None
        self.dbm.view = view_mock



    def tearDown(self):
        pass

    def test_should_create_form_submission_with_entity_id(self):
        form_model = self._create_data_submission_form()
        answers = OrderedDict({"id": "1", "q1": "My Name"})

        form_submission = FormSubmissionFactory().get_form_submission(form_model, answers)

        self.assertEqual(form_submission.form_code, "AIDS")
        self.assertEqual(form_submission.short_code, "1")


    def test_should_create_global_form_submission_location_tree(self):
        form_model = self._construct_global_registration_form()
        submission = OrderedDict({"s": "1", "t": "Reporter", "l": "pune", "m": "1212121212"})
        entity_mock, patcher = self._create_entity_mock()
        location_tree = {1: 2}
        form_submission = FormSubmissionFactory().get_form_submission(form_model, submission,
            location_tree=location_tree)
        data_record_id = form_submission.save(self.dbm)
        patcher.stop()
        self.assertEqual(1, data_record_id)
        self.assertEqual(form_submission.location_tree, location_tree)


    def test_should_do_submission_with_event_time(self):
        form_model=self._create_data_submission_form()
        submission = OrderedDict({"id": "1", "q1": "My Name", "ET": self.event_time_question.validate('01.01.2011')})
        entity_mock,patcher = self._get_entity_mock()

        form_submission = FormSubmissionFactory().get_form_submission(form_model, submission)
        form_submission.save(self.dbm)
        patcher.stop()

        expected_event_time = datetime.datetime(2011, 1, 1, 0, 0)
        self._assert_data_submission_entity_mock(entity_mock, expected_event_time)

    def test_should_do_submission_without_event_time(self):
        form_model = self._create_data_submission_form()
        submission = OrderedDict({"id": "1", "q1": "My Name"})
        entity_mock, patcher = self._get_entity_mock()

        form_submission = FormSubmissionFactory().get_form_submission(form_model, submission)
        form_submission.save(self.dbm)
        patcher.stop()
        self._assert_data_submission_entity_mock(entity_mock)

    #TODO : struggled and Not happy with they way this test has been written. indicates that some basic design flaw.
    #need to correct this
    def test_should_do_submission_for_global_registration_form(self):
        form_model = self._construct_global_registration_form()
        submission = OrderedDict({"s": "1", "t": "Reporter", "l": "pune", "m": "1212121212"})
        entity_mock, patcher = self._create_entity_mock()
        form_submission = FormSubmissionFactory().get_form_submission(form_model, submission)
        data_record_id = form_submission.save(self.dbm)
        patcher.stop()
        self.assertEqual(1, data_record_id)

    def _assert_data_submission_entity_mock(self, entity_mock, event_time=None):
        submission_values = [('Name', 'My Name', self.ddtype_mock)]
        if event_time is not None:
            submission_values.append(("Event time",event_time,self.ddtype_mock))
        submission_values.append(('entity_question', '1', self.ddtype_mock))

        submission_information = {'form_code': u'AIDS'}
        entity_mock.add_data.assert_called_once_with(data=submission_values,
            event_time=event_time, submission=submission_information)

    def _get_entity_mock(self):
        entity_patcher = patch('mangrove.form_model.form_model.entity.get_by_short_code')
        entity_patcher_mock = entity_patcher.start()
        entity_mock = Mock(spec=Entity)
        entity_patcher_mock.return_value = entity_mock
        return entity_mock, entity_patcher

    def _create_entity_mock(self):
        entity_patcher = patch('mangrove.form_model.form_model.entity.create_entity')
        entity_patcher_mock = entity_patcher.start()
        entity_mock = Mock(spec=Entity)
        entity_patcher_mock.return_value = entity_mock
        entity_mock.add_data.return_value = 1
        return entity_mock, entity_patcher

    def _construct_global_registration_form(self):
        mocked_form_model = Mock()
        mocked_form_model.entity_type = GLOBAL_REGISTRATION_FORM_ENTITY_TYPE
        mocked_form_model.entity_question.code = 's'
        return mocked_form_model
