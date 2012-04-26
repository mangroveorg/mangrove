from collections import OrderedDict
from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.form_model import FormModel, FormSubmissionFactory, FormSubmission
from mangrove.transport.facade import Request, TransportInfo
from mangrove.transport.player.player import WebPlayer, XFormPlayer
from mangrove.utils.test_utils.dummy_location_tree import DummyLocationTree

class TestXFormPlayer(TestCase):

    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.player = XFormPlayer(self.dbm)
        transport = TransportInfo(transport="xform", source="1234", destination="5678")
        message = '<xml></xml>'
        self.request = Request(message=message,transportInfo=transport)

    def test_should_delegate_accept_to_web_player(self):
        with patch.object(WebPlayer, 'accept') as accept_mock:
            self.player.accept(self.request)
            accept_mock.assert_called_once_with(self.player,self.request)

    def test_should_parse_xml_and_delegate_dict_parsing_to_web_player(self):
        with patch.object(WebPlayer, '_parse') as parse_mock:
            with patch('mangrove.transport.player.player.xmldict.xml_to_dict') as xml_to_dict_mock:
                mock_submission_dict = Mock(spec=dict)
                xml_to_dict_mock.return_value = {'data' : mock_submission_dict}

                self.player._parse(self.request.message)

                xml_to_dict_mock.assert_called_once_with(self.request.message)
                parse_mock.assert_called_once_with(self.player, mock_submission_dict)
