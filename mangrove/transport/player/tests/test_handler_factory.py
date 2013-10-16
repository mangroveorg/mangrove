
from unittest import TestCase
from mock import Mock
from mangrove.contrib.deletion import ENTITY_DELETION_FORM_CODE
from mangrove.transport.player.handler import handler_factory, DeleteHandler, CreateEntityHandler

class TestHandlerFactory(TestCase):
    def setUp(self):
        self.dbm = Mock()
        self.form_model = Mock()
        self.form_model.form_code = ENTITY_DELETION_FORM_CODE

    def test_should_get_delete_handler_for_delete_form_model(self):
        self.assertIsInstance(handler_factory(self.dbm, self.form_model), DeleteHandler)

    def test_should_get_submission_handler_for_all_other_form_models(self):
        self.form_model.form_code = None
        self.assertIsInstance(handler_factory(self.dbm, self.form_model), CreateEntityHandler)


