# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.form_model import create_default_reg_form_model, _construct_registration_form

class TestFormModel(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock(spec = DatabaseManager)
        self.datadict_patcher = patch("mangrove.form_model.form_model.get_or_create_data_dict")
        self.datadict_mock = self.datadict_patcher.start()
        self.datadict_mock.return_value = Mock(spec=DataDictType)

    def tearDown(self):
        self.datadict_patcher.stop()

    def test_should_create_registration_form_mode(self):
        form = _construct_registration_form(self.dbm)
        self.assertEqual(6, len(form.fields))
        self.assertEqual("REG",form.form_code)

    def test_registration_form_should_have_entity_type_field(self):
        form = _construct_registration_form(self.dbm)
        field = form.get_field_by_code("T")
        self.assertIsNotNone(field)