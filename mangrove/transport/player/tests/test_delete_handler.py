
from collections import OrderedDict
from unittest import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.form_model import FormModel, SHORT_CODE, ENTITY_TYPE_FIELD_CODE
from mangrove.transport.player.handler import DeleteHandler

class TestDeleteHandler(TestCase):

    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.handler = DeleteHandler(self.dbm)
        self.delete_form = Mock(spec=FormModel)
        self.submission_uuid = '1'
        self.reporter_names = []
        self.void_entity_patcher = patch('mangrove.transport.player.handler.void_entity')
        self.void_entity_mock = self.void_entity_patcher.start()

    def tearDown(self):
        self.void_entity_patcher.stop()

    def test_should_delete_entity_if_it_exists(self):
        cleaned_data = OrderedDict()
        cleaned_data[ENTITY_TYPE_FIELD_CODE] = 'clinic'
        cleaned_data[SHORT_CODE] = 'cli1'
        errors = OrderedDict()
        response = self.handler.handle(self.delete_form,cleaned_data,errors, self.submission_uuid, self.reporter_names)
        self.assertTrue(response.success)
        self.assertEqual(self.reporter_names, response.reporters)
        self.assertEqual('1', response.submission_id)
        self.assertEqual(cleaned_data, response.processed_data)
        self.assertEqual(errors, response.errors)
        self.void_entity_mock.assert_called_once_with(self.dbm, 'clinic', 'cli1')

    def test_should_not_delete_entity_if_it_does_not_exist(self):
        cleaned_data = OrderedDict()
        cleaned_data[ENTITY_TYPE_FIELD_CODE] = 'clinic'
        cleaned_data[SHORT_CODE] = 'cli1'
        errors = OrderedDict()
        errors[ENTITY_TYPE_FIELD_CODE] = 'some error'
        errors[SHORT_CODE] = 'some error'

        response = self.handler.handle(self.delete_form,cleaned_data,errors, self.submission_uuid, self.reporter_names)
        self.assertFalse(response.success)
        self.assertEqual(self.reporter_names, response.reporters)
        self.assertEqual('1', response.submission_id)
        self.assertEqual(cleaned_data, response.processed_data)
        self.assertEqual(errors, response.errors)
        self.assertEqual(0, self.void_entity_mock.call_count)

