# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import os
import unittest
from mangrove.bootstrap import initializer
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.form_model.form_model import get_form_model_by_code


class MangroveTestCase(unittest.TestCase):
    def setUp(self):
        self.db_name = 'mangrove-test-' + str(os.getpid())
        self.manager = get_db_manager('http://localhost:5984/', self.db_name)
        initializer._create_views(self.manager)


    def tearDown(self):
        self.manager = get_db_manager('http://localhost:5984/', self.db_name)
        _delete_db_and_remove_db_manager(self.manager)
        get_form_model_by_code.clear()


