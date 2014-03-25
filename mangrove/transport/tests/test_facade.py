import unittest
from mock import Mock, patch
from mangrove.errors.MangroveException import DataObjectNotFound
from mangrove.form_model.form_submission import FormSubmission
from mangrove.form_model.field import HierarchyField, GeoCodeField, ShortCodeField
from mangrove.form_model.form_model import LOCATION_TYPE_FIELD_NAME
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.form_model.field import TextField
from mangrove.form_model.form_model import FormModel
from mangrove.utils.test_utils.dummy_location_tree import DummyLocationTree
from mangrove.utils.types import is_empty
from mangrove.transport.work_flow import ActivityReportWorkFlow, RegistrationWorkFlow
from mangrove.transport.contract.response import create_response_from_form_submission


class TestRegistrationWorkFlow(unittest.TestCase):

    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.form_model_mock = Mock(spec=FormModel)
        self.form_model_mock.get_field_by_name = self._location_field
        self.get_entity_count = patch('mangrove.transport.work_flow.get_entity_count_for_type', new=dummy_get_entity_count_for_type,spec=True)
        self.get_by_short_code_include_voided = patch('mangrove.transport.work_flow.get_by_short_code_include_voided', new=dummy_get_by_short_code_include_voided)
        self.get_by_short_code_include_voided.start()
        self.get_entity_count.start()

    def tearDown(self):
        self.get_entity_count.stop()

    def test_should_generate_default_code_if_short_code_is_empty(self):
        registration_work_flow = RegistrationWorkFlow(self.dbm, self.form_model_mock, DummyLocationTree())
        self.form_model_mock.get_short_code = Mock(return_value=None)
        self.form_model_mock.entity_type=['clinic']
        self.form_model_mock.entity_questions = [ShortCodeField(name="entity question", code="s", label="bar")]
        values = registration_work_flow.process({'t': 'clinic', 'l':'pune'})
        self.assertEqual({'s': 'cli1', 't': 'clinic', 'l': ['pune', 'mh', 'india']}, values)

    def test_should_set_location_data(self):
        self._generate_short_code_if_empty_patch = patch('mangrove.transport.work_flow.RegistrationWorkFlow._generate_short_code_if_empty')
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

def dummy_get_by_short_code_include_voided(dbm,short_code,entity_type):
    raise DataObjectNotFound("Entity","Not found",short_code)

def dummy_get_entity_count_for_type(dbm, entity_type):
    return 0

def dummy_get_location_hierarchy(foo):
    return [u'arantany']


class TestResponse(unittest.TestCase):

    def test_should_initialize_response(self):
        response = create_response_from_form_submission(reporters=None, form_submission=None)
        self.assertFalse(response.success)
        self.assertTrue(is_empty(response.errors))
        self.assertTrue(is_empty(response.reporters))

    def test_should_initialize_response_with_reporters(self):
        reporters=[1]
        response = create_response_from_form_submission(reporters=reporters, form_submission=None)
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


        response = create_response_from_form_submission(reporters=None, form_submission=form_submission_mock)
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


