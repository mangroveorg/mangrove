# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from collections import OrderedDict
from unittest.case import TestCase, SkipTest
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType
from mangrove.datastore.entity import Entity
from mangrove.form_model.field import TextField, DateField
from mangrove.form_model.form_model import FormModel, FormSubmission


class TestFormSubmission(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.ddtype_mock = Mock(spec=DataDictType)

        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
            language="eng", entity_question_flag=True, ddtype=self.ddtype_mock)
        question2 = TextField(name="Name", code="Q1", label="What is your name",
            defaultValue="some default value", language="eng", ddtype=self.ddtype_mock)
        self.event_time_field_code = "ET"
        self.event_time_question = DateField(name="Event time", code=self.event_time_field_code, label="Event time field",
            date_format="dd.mm.yyyy", ddtype=self.ddtype_mock, required=False, event_time_field_flag=True)

        self.form_model = FormModel(self.dbm, entity_type=["Clinic"], name="aids", label="Aids form_model",
            form_code="AIDS", type='survey',
            fields=[question1, question2, self.event_time_question])

    def tearDown(self):
        pass

    def test_should_create_form_submission_with_entity_id(self):
        answers = OrderedDict({"id": "1", "q1": "My Name"})

        form_submission = FormSubmission(self.form_model, answers)

        self.assertEqual(form_submission.form_code, "AIDS")
        self.assertEqual(form_submission.short_code, "1")



    def test_should_do_submission_with_event_time(self):
        event_time_answer = self.event_time_question.validate('01.01.2012')
        submission = OrderedDict({"id": "1", "q1": "My Name", "ET": event_time_answer})
        entity_mock,patcher = self._get_entity_mock()

        form_submission = FormSubmission(self.form_model, submission)
        form_submission.save(self.dbm)
        patcher.stop()

        self._assert_entity_mock(entity_mock, event_time_answer)

    def test_should_do_submission_without_event_time(self):
        submission = OrderedDict({"id": "1", "q1": "My Name"})
        entity_mock,patcher = self._get_entity_mock()

        form_submission = FormSubmission(self.form_model, submission)
        form_submission.save(self.dbm)
        patcher.stop()
        self._assert_entity_mock(entity_mock)

    def _assert_entity_mock(self, entity_mock,event_time=None):

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
        return entity_mock,entity_patcher
