from unittest.case import TestCase
from mock import Mock
from nose.case import Test
from mangrove.datastore.entity import Entity
from mangrove.form_model.field import TextField
from mangrove.form_model.form_model import FormModel
from mangrove.transport.facade import ActivityReportWorkFlow

class TestActivityWorkFlow(TestCase):
    def setUp(self):
        self.form_model_mock = Mock(spec=FormModel)
        self.reporter_entity_mock = Mock(spec=Entity)

    def tearDown(self):
        pass

    def test_should_generate_default_code_if_short_code_is_empty_and_entity_is_reporter(self):
        activity_report = ActivityReportWorkFlow(form_model=self.form_model_mock, reporter_entity= self.reporter_entity_mock)
        self.form_model_mock.get_short_code = Mock(return_value=None)
        self.form_model_mock.entity_defaults_to_reporter = Mock(return_value=True)
        self.form_model_mock.entity_question = TextField(name="entity question", code="foo", label="bar", ddtype=Mock())
        self.reporter_entity_mock.short_code = 2
        self.assertEquals({'l':'None', 'foo':2}, activity_report.process({'l':'None'}))

    def test_should_not_generate_code_if_form_model_has_code_and_entity_type_is_reporter(self):
        activity_report = ActivityReportWorkFlow(form_model=self.form_model_mock, reporter_entity= self.reporter_entity_mock)
        self.form_model_mock.get_short_code = Mock(return_value='1')
        self.form_model_mock.entity_defaults_to_reporter = Mock(return_value=True)
        self.form_model_mock.entity_question = TextField(name="entity question", code="foo", label="bar", ddtype=Mock())
        self.assertEquals({'l':'None'}, activity_report.process({'l':'None'}))

    def test_should_not_generate_code_if_form_model_has_code_and_entity_type_is_not_reporter(self):
        activity_report = ActivityReportWorkFlow(form_model=self.form_model_mock, reporter_entity= self.reporter_entity_mock)
        self.form_model_mock.get_short_code = Mock(return_value='1')
        self.form_model_mock.entity_defaults_to_reporter = Mock(return_value=False)
        self.form_model_mock.entity_question = TextField(name="entity question", code="foo", label="bar", ddtype=Mock())
        self.assertEquals({'l':'None'}, activity_report.process({'l':'None'}))

    def test_should_not_generate_code_if_entity_type_is_reporter_and_form_model_dont_have_code(self):
        activity_report = ActivityReportWorkFlow(form_model=self.form_model_mock, reporter_entity= self.reporter_entity_mock)
        self.form_model_mock.get_short_code = Mock(return_value=None)
        self.form_model_mock.entity_defaults_to_reporter = Mock(return_value=False)
        self.form_model_mock.entity_question = TextField(name="entity question", code="foo", label="bar", ddtype=Mock())
        self.assertEquals({'l':'None'}, activity_report.process({'l':'None'}))

