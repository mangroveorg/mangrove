# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.datastore.database import get_db_manager
from mangrove.datastore.database import _delete_db_and_remove_db_manager as trash_db
from mangrove.datastore.aggregationtree import AggregationTree as ATree, get as get_atree, \
    get_by_id, get_by_name, _blow_tree_cache


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

    def test_load_by_name_id(self):
        by_name = {}
        by_id = {}
        for name in ('t1', 't2', 't3', 't4'):
            t = ATree(self.dbm, name)
            id = t.save()
            by_name[name] = (id, name)
            by_id[id] = (id, name)

        for name in by_name:
            self.assertTrue(get_by_name(self.dbm, name)._doc.id == by_name[name][0])

        for id in by_id:
            self.assertTrue(get_by_id(self.dbm, id)._doc.name == by_id[id][1])

        with self.assertRaises(KeyError):
            get_by_id(self.dbm, 'no exist')

        with self.assertRaises(KeyError):
            get_by_name(self.dbm, 'no exist')

    def test_load_by_name_create(self):
        # prove it doesn't exist by calling and getting exception
        with self.assertRaises(KeyError):
            get_by_name(self.dbm, 'foobarbaz')

        # now call with create
        t = get_by_name(self.dbm, 'foobarbaz', get_or_create=True)
        self.assertTrue(t.name == 'foobarbaz')

        # now blow cache and get again
        _blow_tree_cache()
        t = get_by_name(self.dbm, 'foobarbaz')
        self.assertTrue(t.name == 'foobarbaz')