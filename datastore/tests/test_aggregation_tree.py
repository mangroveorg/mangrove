# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.datastore.database import get_db_manager
from mangrove.datastore.database import _delete_db_and_remove_db_manager as trash_db
from mangrove.datastore.aggregationtree import AggregationTree as ATree


class TestAggregationTrees(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='tree_test')

    def tearDown(self):
        trash_db(self.dbm)

    def test_creation(self):
        t1 = ATree(self.dbm, '_test_tree')
        self.assertIsInstance(t1, ATree)
