from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.transport.player.player import  XFormPlayer, Player
from mangrove.transport.contract.transport_info import TransportInfo
from mangrove.transport.contract.request import Request

class TestXFormPlayer(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.player = XFormPlayer(self.dbm)
        transport = TransportInfo(transport="xform", source='mail@domain.com', destination="5678")
        message = '<xml></xml>'
        self.request = Request(message=message, transportInfo=transport)
        self.xform_parser_patcher = patch("mangrove.transport.player.player.XFormParser.parse")
        self.mock_parser = self.xform_parser_patcher.start()
        self.form_model_patcher = patch('mangrove.transport.player.player.get_form_model_by_code')
        self.mock_get_form_model = self.form_model_patcher.start()


    def tearDown(self):
        self.xform_parser_patcher.stop()

    def test_should_make_successful_submission(self):
        submission_values = {'submissionValues': 'values'}
        form_code = 'formCode'
        self.mock_parser.return_value = form_code, submission_values
        mock_form_model = Mock()
        self.mock_get_form_model.return_value = mock_form_model
        mock_form_model.get_short_code.return_value = ""
        mock_form_model.entity_question.code = 'eid'
        mock_form_model.entity_defaults_to_reporter.return_value = True
        with patch.object(Player, '_create_submission') as mock_create_submission:
            with patch.object(Player, 'submit') as mock_submission:
                submission = Mock()
                mock_create_submission.return_value = submission
                self.player.accept(self.request)
                self.mock_parser.assert_called_once_with(self.request.message)
                mock_create_submission.assert_called_once_with(self.request.transport, form_code,
                        {'submissionValues': 'values'})
                mock_submission.assert_called_once_with(mock_form_model, {'submissionValues': 'values'}
                    , submission,[])