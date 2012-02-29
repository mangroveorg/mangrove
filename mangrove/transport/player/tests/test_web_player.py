from collections import OrderedDict
from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.form_model import FormModel, FormSubmissionFactory, FormSubmission
from mangrove.transport.facade import Request, TransportInfo
from mangrove.transport.player.player import WebPlayer

class TestWebPlayer(TestCase):

    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.web_player = WebPlayer(self.dbm, DummyLocationTree(), get_location_hierarchy)
        self.transport = TransportInfo(transport="web", source="1234", destination="5678")
        self.message = {'form_code':'reg', 'n':'subject_name', 't':'clinic', 'l':'Pune'}
        self._mock_form_model()

    def _mock_form_model(self):
        self.form_model_mock = Mock(spec=FormModel)
        self.form_model_mock.is_inactive.return_value = False
        self.get_form_model_mock_patcher = patch('mangrove.transport.player.player.get_form_model_by_code')
        get_form_model_mock = self.get_form_model_mock_patcher.start()
        get_form_model_mock.return_value = self.form_model_mock
        self.form_model_mock.is_valid.return_value = OrderedDict(), OrderedDict()

        self.form_submission_mock = Mock(spec=FormSubmission)
        self.form_model_mock.is_valid.return_value = OrderedDict(), OrderedDict()
        self.form_submission_mock = Mock(spec=FormSubmission)
        self.form_submission_mock.is_valid = True
        self.form_submission_mock.errors = OrderedDict()
        self.form_submission_mock.data_record_id = ''
        self.form_submission_mock.form_model = self.form_model_mock
        self.form_submission_mock.short_code = ''
        self.form_submission_mock.entity_type = ['']



    def tearDown(self):
        self.get_form_model_mock_patcher.stop()

    def test_should_submit_if_parsing_is_successful(self):
        with patch.object(FormSubmissionFactory, 'get_form_submission') as get_form_submission_mock:
            get_form_submission_mock.return_value = self.form_submission_mock
            response = self.web_player.accept(Request(message=self.message, transportInfo=self.transport))
            self.form_submission_mock.save.assert_called_once_with(self.dbm)
            self.assertEqual('', response.datarecord_id)
            self.assertEqual([''], response.entity_type)


def get_location_hierarchy(foo):
    return ["no_hierarchy"]

class DummyLocationTree(object):
    def get_location_hierarchy_for_geocode(self, lat, long ):
        return ['madagascar']

    def get_centroid(self, location_name, level):
        return 60, -12