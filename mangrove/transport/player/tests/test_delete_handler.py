# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest import TestCase
from mock import patch, Mock, self
from mangrove.datastore.database import DatabaseManager
from mangrove.transport.player.handler import DeleteHandler
from mangrove.transport.player.parser import DeleteRequestParser
from mangrove.transport.facade import Request

class TestDeleteHandler(TestCase):

    def setUp(self):
        self.manager = Mock(spec=DatabaseManager)
        self.delete_handler = DeleteHandler(self.manager)
        self.submission_patcher = patch('mangrove.transport.player.handler.Submission')
        self.invalidate_entity_patcher = patch('mangrove.transport.player.handler.invalidate_entity')
        self.submission_mock = self.submission_patcher.start()
        self.invalidate_entity_mock = self.invalidate_entity_patcher.start()

    def tearDown(self):
        self.submission_patcher.stop()
        self.invalidate_entity_patcher.stop()

    def test_should_parse_the_request(self):
        message = 'delete entity_type entity_id'
        command = 'delete'
        values = {'entity_type': 'entity_type', 'entity_id': 'entity_id'}
        transportInfo = Mock()
        request = Request(message=message, transportInfo=transportInfo)
        mock_submission = Mock()
        self.submission_mock.return_value = mock_submission

        with patch.object(DeleteRequestParser, 'parse') as parse_mock:
            parse_mock.return_value = command,values
            self.delete_handler.handle(request)
            parse_mock.assert_called_once_with(message)
        self.submission_mock.assert_called_once_with(self.manager, transportInfo, command, values)
        mock_submission.save.assert_called_once_with()
        self.invalidate_entity_mock.assert_called_once_with(self.manager, 'entity_type', 'entity_id')
