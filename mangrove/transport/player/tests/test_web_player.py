from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.form_model import FormModel
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
        self.get_form_model_mock_patcher = patch('mangrove.transport.player.player.get_form_model_by_code')
        get_form_model_mock = self.get_form_model_mock_patcher.start()
        get_form_model_mock.return_value = self.form_model_mock

    def tearDown(self):
        self.get_form_model_mock_patcher.stop()

    def test_should_submit_if_parsing_is_successful(self):
        self.web_player.accept(Request(message=self.message, transportInfo=self.transport))
        self.assertEqual(1, self.form_model_mock.submit.call_count)


def get_location_hierarchy(foo):
    return ["no_hierarchy"]

class DummyLocationTree(object):
    def get_location_hierarchy_for_geocode(self, lat, long ):
        return ['madagascar']

    def get_centroid(self, location_name, level):
        return 60, -12