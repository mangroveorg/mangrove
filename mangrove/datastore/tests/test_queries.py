# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.entity import create_entity
from mangrove.datastore.entity_type import define_type
from mangrove.datastore.queries import get_entity_count_for_type
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestQueries(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)

    def tearDown(self):
        MangroveTestCase.tearDown(self)


    def test_get_entity_count_for_type(self):
        entity_type = "Clinic"
        define_type(self.manager,[entity_type])
        create_entity(self.manager, [entity_type],"1")
        self.assertEqual(1,get_entity_count_for_type(self.manager,entity_type))


