
import os
import unittest
from mangrove.bootstrap import initializer
from mangrove.datastore.cache_manager import get_cache_manager
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.utils.test_utils.database_utils import uniq


class MangroveTestCase(unittest.TestCase):
    def setUp(self):
        self.db_name = uniq('mangrove-test')
        self.manager = get_db_manager('http://localhost:5984/', self.db_name)
        initializer._create_views(self.manager)


    def tearDown(self):
        self.manager = get_db_manager('http://localhost:5984/', self.db_name)
        _delete_db_and_remove_db_manager(self.manager)
        get_cache_manager().flush_all()


