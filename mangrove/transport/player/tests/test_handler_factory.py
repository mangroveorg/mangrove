# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest import TestCase
from mock import Mock
from mangrove.contrib.deletion import ENTITY_DELETION_FORM_CODE
from mangrove.transport.player.handler import handler_factory, DeleteHandler, SubmissionHandler

class TestHandlerFactory(TestCase):
    def setUp(self):
        self.dbm = Mock()

    def test_should_get_delete_handler_for_delete_form_model(self):
        self.assertIsInstance(handler_factory(self.dbm, ENTITY_DELETION_FORM_CODE), DeleteHandler)

    def test_should_get_submission_handler_for_all_other_form_models(self):
        self.assertIsInstance(handler_factory(self.dbm, 'test_form_model'), SubmissionHandler)


