# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest import TestCase
from mock import patch, Mock
from mangrove.transport.player.handler import DeleteHandler
from mangrove.transport.player.parser import DeleteRequestParser
from mangrove.transport.facade import Request

class TestDeleteHandler(TestCase):
    def test_should_parse_the_request(self):
        message = 'delete entity_type entity_id'
        request = Request(message=message, transportInfo=Mock())
        delete_handler = DeleteHandler(request)
        with patch.object(DeleteRequestParser, 'parse') as parse_mock:
            delete_handler.handle()
            parse_mock.assert_called_once_with(message)


