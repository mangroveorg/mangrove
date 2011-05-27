# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mock import Mock
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import generate_short_code


class TestEntityShortCode(unittest.TestCase):
    def test_should_generate_short_id(self):
        manager = Mock(spec=DatabaseManager)
        manager.load_all_rows_in_view.return_value=[{"key": [["Reporter"]], "value": 3}]
        id = generate_short_code(manager, entity_type=["Reporter"])
        self.assertEqual("REP4", id)

    def test_should_generate_short_code_when_the_entity_type_has_no_instances(self):
        manager = Mock(spec=DatabaseManager)
        manager.load_all_rows_in_view.return_value = []
        id = generate_short_code(manager, entity_type=["Clinic"])
        self.assertEqual("CLI1", id)

    def test_should_generate_short_code_with_entity_type(self):
        manager = Mock(spec=DatabaseManager)
        manager.load_all_rows_in_view.return_value = []
        id = generate_short_code(manager, entity_type=["Health Facility","Clinic"])
        self.assertEqual("CLI1", id)
