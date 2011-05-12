# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.datastore.database import get_db_manager
from mangrove.datastore.database import _delete_db_and_remove_db_manager as trash_db
from mangrove.datastore.aggregationtree import AggregationTree as ATree
from mangrove.errors.MangroveException import ObjectNotFound


class TestAggregationTrees(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='tree_test')

    def tearDown(self):
        trash_db(self.dbm)

    def test_instantiation(self):
        t1 = ATree(self.dbm, 'test_tree')
        self.assertIsInstance(t1, ATree)

    def test_save_retrieve(self):
        t1 = ATree(self.dbm, 'test_tree')
        t1.graph.add_edges_from([(ATree.root_id, '1'), ('1', '1.1'), ('1', '1.2'), ('1', '1.3'), ('1.1', '1.1.1')])
        t1.graph.add_path([ATree.root_id, 'a', 'b', 'c', 'd'])
        t1_adj = t1.graph.adj
        t1_id = t1.save()
        self.dbm.blow_cache()
        t2 = self.dbm.get(t1_id, ATree)
        self.assertDictEqual(t1_adj, t2.graph.adj)

    def test_add_path(self):
        t1 = ATree(self.dbm, 'test_add_path_1')
        t1.graph.add_path([ATree.root_id, 1, 2, 3, 4, 5])
        t1_id = t1.save()

        t2 = ATree(self.dbm, 'test_add_path_2')
        t2.add_path([ATree.root_id, 1, 2, 3, 4, 5])
        t2_id = t2.save()

        self.dbm.blow_cache()
        self.assertDictEqual(self.dbm.get(t1_id, ATree).graph.adj, self.dbm.get(t2_id, ATree).graph.adj)

    def test_get_paths(self):
        t = ATree(self.dbm, 'paths_test')

        t.add_path([ATree.root_id, 1, 2, 3])
        t.add_path([1, 1.1])

        expected = [[1], [1, 2], [1, 2, 3], [1, 1.1]]
        tree_paths = t.get_paths()
        for p in expected:
            self.assertIn(p, tree_paths)

    def test_get_leaf_paths(self):
        t = ATree(self.dbm, 'leaf_paths_test')
        paths = [(ATree.root_id, 'a', 'b', 'c', 'd'),
                 (ATree.root_id, 1, 2, 3, 4)]
        for p in paths:
            t.add_path(p)

        tree_paths = t.get_leaf_paths()
        for p in [list(p[1:]) for p in paths]:
            self.assertIn(p, tree_paths)

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

    def test_get_by_name(self):
        name = 'test_tree_name'
        # shouldn't be there
        with self.assertRaises(ObjectNotFound):
            self.dbm.get(name, ATree)

        # now try with get_or_create
        tree = self.dbm.get(name, ATree, get_or_create=True)
        self.assertEqual(tree.name, name)
