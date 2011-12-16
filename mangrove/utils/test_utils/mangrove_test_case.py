# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.bootstrap import initializer
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager

class MangroveTestCase(unittest.TestCase):
    def setUp(self):
        self.manager = get_db_manager('http://localhost:5984/', 'mangrove-test')
        initializer._create_views(self.manager)

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.manager)


  