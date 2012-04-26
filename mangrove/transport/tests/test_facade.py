import unittest
from mock import Mock, patch
from mangrove.form_model.field import HierarchyField, GeoCodeField
from mangrove.form_model.form_model import LOCATION_TYPE_FIELD_NAME, FormSubmission
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.form_model.field import TextField
from mangrove.form_model.form_model import FormModel
from mangrove.transport.facade import ActivityReportWorkFlow, RegistrationWorkFlow, create_response_from_form_submission
from mangrove.utils.test_utils.dummy_location_tree import DummyLocationTree
from mangrove.utils.types import is_empty

class TestActivityWorkFlow(unittest.TestCase):
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

class TestRegistrationWorkFlow(unittest.TestCase):

    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.form_model_mock = Mock(spec=FormModel)
        self.form_model_mock.get_field_by_name = self._location_field
        self.get_entity_count = patch('mangrove.transport.facade.get_entity_count_for_type', new=dummy_get_entity_count_for_type,spec=True)
        self.get_entity_count.start()

    def tearDown(self):
        self.get_entity_count.stop()

    def test_should_generate_default_code_if_short_code_is_empty(self):
        registration_work_flow = RegistrationWorkFlow(self.dbm, self.form_model_mock, DummyLocationTree())
        self.form_model_mock.get_short_code = Mock(return_value=None)
        self.form_model_mock.entity_type=['clinic']
        self.form_model_mock.entity_question = TextField(name="entity question", code="s", label="bar", ddtype=Mock())
        values = registration_work_flow.process({'t': 'clinic', 'l':'pune'})
        self.assertEqual({'s': 'cli1', 't': 'clinic', 'l': ['pune', 'mh', 'india']}, values)

    def test_should_set_location_data(self):
        self._generate_short_code_if_empty_patch = patch('mangrove.transport.facade.RegistrationWorkFlow._generate_short_code_if_empty')
        self._generate_short_code_if_empty_mock = self._generate_short_code_if_empty_patch.start()
        self.process_submission_patch = patch('mangrove.form_model.location.Location.process_submission')
        self.process_submission_mock = self.process_submission_patch.start()
        values = ['a','b']
        RegistrationWorkFlow(self.dbm, self.form_model_mock, DummyLocationTree()).process(values)
        self.assertEquals(1, self.process_submission_mock.call_count)
        self._generate_short_code_if_empty_patch.stop()
        self.process_submission_patch.stop()



    def _location_field(self,*args,**kwargs):
        name = kwargs.get('name')
        if name is LOCATION_TYPE_FIELD_NAME:
            location_field = Mock(spec=HierarchyField)
            location_field.code='l'
            return location_field
        geo_code_field=Mock(spec=GeoCodeField)
        geo_code_field.code='g'
        return geo_code_field


def dummy_get_entity_count_for_type(dbm, entity_type):
    return 0

def dummy_get_location_hierarchy(foo):
    return [u'arantany']


class TestResponse(unittest.TestCase):

    def test_should_initialize_response(self):
        response = create_response_from_form_submission(reporters=None, submission_id=None, form_submission=None)
        self.assertFalse(response.success)
        self.assertTrue(is_empty(response.errors))
        self.assertTrue(is_empty(response.reporters))

    def test_should_initialize_response_with_reporters(self):
        reporters=[1]
        response = create_response_from_form_submission(reporters=reporters, submission_id=None, form_submission=None)
        self.assertEquals(reporters,response.reporters)

    def test_should_initialize_response_from_form_submission(self):
        form_submission_mock = Mock(spec=FormSubmission)
        form_submission_mock.saved=True
        form_submission_mock.errors=[]
        expected_data_record_id = 123
        form_submission_mock.data_record_id= expected_data_record_id
        expected_short_code = 456
        form_submission_mock.short_code= expected_short_code
        expected_cleanned_data = {'a': 1}
        form_submission_mock.cleaned_data= expected_cleanned_data
        form_submission_mock.is_registration=False
        expected_entity_type = 'entity_type'
        form_submission_mock.entity_type= expected_entity_type
        expected_form_code = '1'
        form_model_mock = Mock()
        form_model_mock.form_code = expected_form_code
        form_submission_mock.form_model = form_model_mock


        response = create_response_from_form_submission(reporters=None, submission_id=None, form_submission=form_submission_mock)
        self.assertTrue(response.success)
        self.assertTrue(is_empty(response.errors))
        self.assertTrue(is_empty(response.reporters))
        self.assertTrue(response.success)
        self.assertEquals(expected_data_record_id,response.datarecord_id)
        self.assertEquals(expected_short_code,response.short_code)
        self.assertEquals(expected_cleanned_data,response.processed_data)
        self.assertFalse(response.is_registration)
        self.assertEquals(expected_entity_type,response.entity_type)
        self.assertEquals(expected_entity_type,response.entity_type)
        self.assertEquals(expected_form_code,response.form_code)


