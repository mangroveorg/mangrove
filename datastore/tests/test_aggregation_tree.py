# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
from mangrove.datastore.database import get_db_manager
from mangrove.datastore.database import _delete_db_and_remove_db_manager as trash_db
from mangrove.datastore.aggregationtree import AggregationTree as ATree
from mangrove.errors.MangroveException import  DataObjectNotFound


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
        t1.graph.add_path([ATree.root_id, '1', '2', '3', '4', '5'])
        t1_id = t1.save()

        t2 = ATree(self.dbm, 'test_add_path_2')
        t2.add_path([ATree.root_id, '1', '2', '3', '4', '5'])
        t2_id = t2.save()

        self.dbm.blow_cache()
        self.assertDictEqual(self.dbm.get(t1_id, ATree).graph.adj, self.dbm.get(t2_id, ATree).graph.adj)

    def test_get_paths(self):
        t = ATree(self.dbm, 'paths_test')

        t.add_path([ATree.root_id, '1', '2', '3'])
        t.add_path(['1', '1.1'])

        expected = [['1'], ['1', '2'], ['1', '2', '3'], ['1', '1.1']]
        tree_paths = t.get_paths()
        for p in expected:
            self.assertIn(p, tree_paths)

    def test_add_node_data(self):
        t1 = ATree(self.dbm, 'data_test_tree')
        t1.add_root_path(['1', '2', '3'])
        ddict = {'1': 1, '2': 2}
        t1.set_data_for('1', ddict)
        id = t1.save()

        t2 = self.dbm.get(id, ATree, force_reload=True)
        self.assertDictEqual(ddict, t2.graph.node['1'])

    def node_data_with_non_string_keys_should_raise_valueerror(self):
        t = ATree(self.dbm, 'test_tree')
        t.add_root_pat('a')

        with self.assertRaises(ValueError):
            t.set_data_for('a', {1: 1})

        with self.assertRaises(ValueError):
            t.set_data_for('a', {'1': 1, 1: 1})

    def test_get_node_data(self):
        t1 = ATree(self.dbm, 'data_test_tree')
        t1.add_root_path(['1', '2', '3'])
        ddict = {'1': 1, '2': 2}
        t1.set_data_for('1', ddict)
        id = t1.save()

        t2 = self.dbm.get(id, ATree, force_reload=True)
        self.assertDictEqual(ddict, t2.get_data_for('1'))

    def non_string_node_should_raise_valueerror(self):
        t = ATree(self.dbm, 'test_tree')
        with self.assertRaises(ValueError):
            t.add_root_path([1])

        with self.assertRaises(ValueError):
            t.add_root_path([{1: 1}])

        with self.assertRaises(ValueError):
            t.add_root_path([None])

        with self.assertRaises(ValueError):
            t.add_root_path(['a', 1, 'c'])

    def test_add_path_with_data(self):
        t = ATree(self.dbm, 'data_paths_test')
        path = [('a', {'a': 1}), ('b', {'b': 2}), ('c', {'c': 3, 'c1': 4})]
        t.add_root_path(path)
        id = t.save()
        t2 = self.dbm.get(id, ATree, force_reload=True)

        for node, data in path:
            self.assertDictEqual(t2.get_data_for(node), data)

    def test_get_leaf_paths(self):
        t = ATree(self.dbm, 'leaf_paths_test')
        paths = [(ATree.root_id, 'a', 'b', 'c', 'd'),
                 (ATree.root_id, '1', '2', '3', '4')]
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
            t.add_path(['1', '2', '3', '4'])

    def test_get_by_name(self):
        name = 'test_tree_name'
        # shouldn't be there
        with self.assertRaises(DataObjectNotFound):
            self.dbm.get(name, ATree)

        # now try with get_or_create
        tree = self.dbm.get(name, ATree, get_or_create=True)
        self.assertEqual(tree.name, name)

    def test_add_child(self):
        t = ATree(self.dbm, 'child_test')
        t.add_child(t.root_id, 'foo')
        t.add_child('foo', 'bar')
        t.add_child('foo', 'baz')
        t.add_child('bar', 'bunk')
        id = t.save()
        t2 = self.dbm.get(id, ATree, force_reload=True)

        expected = [['foo'], ['foo', 'bar'], ['foo', 'baz'], ['foo', 'bar', 'bunk']]
        expected.sort()
        paths = t2.get_paths()
        self.assertEqual(sorted(paths), expected)
        with self.assertRaises(ValueError):
            t2.add_child('not-in-tree', 'foo')

    def test_get_children(self):
        t = ATree(self.dbm, 'children_test')
        t.add_root_path(['a', 'b'])
        children = ['c1', 'c2', 'c3', 'c4']
        children.sort()
        for c in children:
            t.add_child('b', c)
        id = t.save()
        t2 = self.dbm.get(id, ATree, force_reload=True)
        self.assertEqual(t2.children_of('a'), ['b'])
        self.assertEqual(sorted(t2.children_of('b')), children)
        with self.assertRaises(ValueError):
            t2.children_of('not-in-tree')

    def test_parent_of(self):
        t = ATree(self.dbm, 'children_test')
        t.add_root_path(['a', 'b', 'c'])
        id = t.save()
        t2 = self.dbm.get(id, ATree, force_reload=True)
        self.assertIsNone(t2.parent_of(t2.root_id))
        self.assertEqual(t2.parent_of('a'), t2.root_id)
        self.assertEqual(t2.parent_of('c'), 'b')
        with self.assertRaises(ValueError):
            t2.parent_of('not-in-tree')

    def test_ancestors_of(self):
        t = ATree(self.dbm, 'children_test')
        t.add_root_path(['a', 'b', 'c'])
        id = t.save()
        t2 = self.dbm.get(id, ATree, force_reload=True)
        self.assertEqual(t2.ancestors_of('a'), [])
        self.assertEqual(t2.ancestors_of('b'), ['a'])
        self.assertEqual(t2.ancestors_of('c'), ['a', 'b'])
        with self.assertRaises(ValueError):
            t2.ancestors_of('not-in-tree')
