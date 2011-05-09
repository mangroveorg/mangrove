# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.datastore.database import get_db_manager
from mangrove.datastore.database import _delete_db_and_remove_db_manager as trash_db
from mangrove.datastore.aggregationtree import AggregationTree as ATree, get as get_atree


class TestAggregationTrees(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='tree_test')

    def tearDown(self):
        trash_db(self.dbm)

    def test_instantiation(self):
        t1 = ATree(self.dbm, '_test_tree')
        self.assertIsInstance(t1, ATree)

    def test_save_retrieve(self):
        t1 = ATree(self.dbm, '_test_tree')
        t1.graph.add_edges_from([(ATree.root_id, '1'), ('1', '1.1'), ('1', '1.2'), ('1', '1.3'), ('1.1', '1.1.1')])
        t1.graph.add_path([ATree.root_id, 'a', 'b', 'c', 'd'])
        t1_adj = t1.graph.adj
        t1_id = t1.save()
        t2 = get_atree(self.dbm, t1_id)
        self.assertDictEqual(t1_adj, t2.graph.adj)

    def test_add_path(self):
        t1 = ATree(self.dbm, '_test_add_path_1')
        t1.graph.add_path([ATree.root_id, 1, 2, 3, 4, 5])
        t1_id = t1.save()

        t2 = ATree(self.dbm, '_test_add_path_2')
        t2.add_path([ATree.root_id, 1, 2, 3, 4, 5])
        t2_id = t2.save()

        self.assertDictEqual(get_atree(self.dbm, t1_id).graph.adj, get_atree(self.dbm, t2_id).graph.adj)

    def test_add_path_bad_args(self):
        # blank path
        with self.assertRaises(AssertionError):
            t = ATree(self.dbm, '_test_tree')
            t.add_path(None)

        # path is not a sequence
        with self.assertRaises(AssertionError):
            t = ATree(self.dbm, '_test_tree')
            t.add_path('foo')

        # path is not a sequence
        with self.assertRaises(AssertionError):
            t = ATree(self.dbm, '_test_tree')
            t.add_path(1)

        # first path item not in graph
        with self.assertRaises(ValueError):
            t = ATree(self.dbm, '_test_tree')
            t.add_path([1, 2, 3, 4])

