from collections import OrderedDict
from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.form_model import FormModel, FormSubmissionFactory, FormSubmission
from mangrove.transport.facade import Request, TransportInfo
from mangrove.transport.player.player import WebPlayer
from mangrove.utils.test_utils.dummy_location_tree import DummyLocationTree

def mock_form_submission(form_model_mock):
    form_submission_mock = Mock(spec=FormSubmission)
    form_submission_mock.is_valid = True
    form_submission_mock.errors = OrderedDict()
    form_submission_mock.data_record_id = ''
    form_submission_mock.form_model = form_model_mock
    form_submission_mock.short_code = ''
    form_submission_mock.entity_type = ['']
    return form_submission_mock


class TestWebPlayer(TestCase):

    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.web_player = WebPlayer(self.dbm, location_tree=DummyLocationTree())
        self.transport = TransportInfo(transport="web", source="1234", destination="5678")
        self.message = {'form_code':'reg', 'n':'subject_name', 't':'clinic', 'l':'Pune'}
        self._mock_form_model()

    def _mock_form_model(self):
        self.form_model_mock = Mock(spec=FormModel)
        self.form_model_mock.is_inactive.return_value = False
        self.get_form_model_mock_patcher = patch('mangrove.transport.player.player.get_form_model_by_code')
        get_form_model_mock = self.get_form_model_mock_patcher.start()
        get_form_model_mock.return_value = self.form_model_mock
        self.form_model_mock.validate_submission.return_value = OrderedDict(), OrderedDict()

        self.form_submission_mock = mock_form_submission(self.form_model_mock)



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

