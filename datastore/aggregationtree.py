# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from threading import Lock

import networkx as nx

from mangrove.utils.types import is_not_empty, is_sequence, is_string
from documents import AggregationTreeDocument
from database import DataObject


class AggregationTree(DataObject):
    '''
    Representation of an aggregation tree.

    In memory this utilizes the NetworkX graph library with each node
    being a dict

    The tree is represented in Couch as dicts of dicts under the
    attribute '_root'

    Each tree has a unique _id which should be a memorable name like
    'geographic_boundaries'

    Each node in the tree is a dict of arbitrary attributes a special
    '_children' attribute that holds the child nodes.

    The node's name is the node's key in the parent dict or '__root'
    for the root node

    So a tree with a partial list of countries and states/provinces of
    this form (in pseudo-lisp-code):

    ((India(Maharashtra, Kerala, Karnataka)), (US(California(SF), Ohio)))

    would look like this::

        {
        _id: _geo
        _root: {
                children: {
                            India: { _children: { Maharashtra: {}}, {Kerala: {}}, {Karnataka: {}}},,
                            US: {_children: { {California: {_children: {SF: {}}}}, {Ohio: {}}},
                          }
                }
        }

    NOTE: Node names must be STRINGS because of JSON encoding issues for couch
    '''
    __document_class__ = AggregationTreeDocument
    root_id = '__root'

    def __init__(self, dbm, id=None):
        '''
        Note: _document is for 'protected' factory methods. If it is passed in the other
        arguments are ignored.

        '''
        assert (id is None or is_not_empty(id))

        DataObject.__init__(self, dbm)
        self.graph = None

        # being constructed from DB? If so, no more work here
        if id is None:
            return

        # ok, newly constructed, so set up a new Document
        self._set_document(AggregationTreeDocument(id=id))

    def _set_document(self, document):
        DataObject._set_document(self, document)
        self._sync_doc_to_graph()

    def save(self):
        id = None
        with Lock():
            self._sync_graph_to_doc()
            id = DataObject.save(self)
        return id

    @property
    def name(self):
        return self.id

    def get_data_for(self, node):
        assert is_string(node)
        return self.graph.node[node]

    def set_data_for(self, node, dikt):
        '''
        Note: all keys in the data dictionary 'dikt' must be strings

        If not, this raises a value error
        '''
        assert is_string(node)
        if not self._verify_dict_keys_are_strings(dikt):
            raise ValueError('Keys in a nodes data-dictionary must be strings')
        self.graph.node[node] = dikt

    def get_paths(self):
        '''
        Returns a list of lists, each one a path from root to every node, with root removed.

        So a simple tree of ROOT->A->B->C returns [[A],[A,B], [A,B,C]]

        Use this method if every node has meaning, e.g. HEALTH FAC->HOSPITAL->REGIONAL

        '''
        # TODO: hold this as a cache that is blown by Add Path
        return [p[1:] for p in nx.shortest_path(self.graph, AggregationTree.root_id, ).values() if is_not_empty(p[1:])]

    def get_leaf_paths(self):
        '''
        Returns a list of lists for all unique paths from root to leaves.

        Paths do not include ROOT and start one level below root

        '''

        # TODO: this is a hacky, probably really slow way to do ths. I need to either find the fast way or cache this.
        # But it is a crazy list comprehension ;-)
        return [nx.shortest_path(self.graph, AggregationTree.root_id, n)[1:] for n in
                [n for n in self.graph.nodes() if n != AggregationTree.root_id and self.graph.degree(n) == 1]]

    def _verify_dict_keys_are_strings(self, dikt):
        '''
        Returns True if all keys are strings, false otherwise

        if 'None' is passed, returns True 'cause there are no keys to NOT be strings!
        '''
        if dikt is not None:
            for k in dikt.keys():
                if not is_string(k):
                    return False
        return True

    def _add_node(self, name, data=None):
        '''
        Adds a node and data the tree.

        NOTE: Because of JSON encoding issues, the node Names and all data dict keys must be strings.
        If not a ValueError is raised!

        '''
        assert data is None or isinstance(data, dict)
        if not is_string(name):
            raise ValueError('Node names must be strings')

        if not self._verify_dict_keys_are_strings(data):
            raise ValueError('Keys in a nodes data-dictionary must be strings')

        self.graph.add_node(name, data)

    def add_child(self, parent, child, data=None):
        '''raises value error if parent not in tree'''
        if parent not in self.graph:
            raise ValueError('"%s" not found in graph' % parent)

        self._add_node(child, data)
        self.graph.add_edge(parent, child)

    def remove_node(self, node):
        if node not in self.graph:
            raise ValueError("Node named: '%s' not in graph" % node)

        self.graph.remove_node(node)

    def children_of(self, node):
        if node not in self.graph:
            raise ValueError("Node named: '%s' not in graph" % node)

        return self.graph.successors(node)

    def parent_of(self, node):
        if node not in self.graph:
            raise ValueError("Node named: '%s' not in graph" % node)

        p = self.graph.predecessors(node)
        return (None if len(p) == 0 else p[0])

    def ancestors_of(self, node):
        a = []
        while True:
            p = self.parent_of(node)
            if p == self.root_id:
                break
            a.append(p)
            node = p
        a.reverse()
        return a

    def add_path(self, nodes):
        '''Adds a path to the tree.

        If the first item in the path is AggregationTree.root_id, this will be added at root.

        Otherwise, the method attempts to find the first (depth first search) occurrence of the first element
        in the sequence, and adds the path there.

        The 'nodes' list can contain tuples of the form '(node_name, dict)' to associate data
        with the nodes.
        e.g. add_path('a', ('b', {size: 10}), 'c')

        Raises a 'ValueError' if the path does NOT start with root and the first item cannot be found.
        '''

        assert is_sequence(nodes) and is_not_empty(nodes)

        first = (nodes[0][0] if is_sequence(nodes[0]) else nodes[0])
        if not first in self.graph:
            raise ValueError('First item in path: %s not in Tree.' % first)

        # iterate, add nodes, and pull out path
        path = []
        for n in nodes:
            data = None
            name = None
            if is_sequence(n):
                name = n[0]
                data = n[1]
            else:
                name = n

            self._add_node(name, data)
            path.append(name)

        # add the path
        self.graph.add_path(path)

    def add_root_path(self, path):
        '''Convenience function for adding this path starting at "root"'''
        self.add_path([self.root_id] + path)

    def _sync_doc_to_graph(self):
        '''Converts internal CouchDB document dict into tree graph'''

        assert self._doc is not None

        def build_graph(graph, parent_id, current_id, current_dict):
            # shallow copy current dict for attributes
            attrs = dict(current_dict)
            children = None

            # make sure not already there...
            if current_id in graph:
                raise ValueError('Attempting to add multiple nodes to tree with same _id: %s' % current_id)

            try:
                children = attrs.pop('_children')
            except KeyError:
                # no problem, it's a terminal node with no children
                pass

            graph.add_node(current_id, attrs)
            if parent_id is not None:
                graph.add_edge(parent_id, current_id)

            # now recurse
            if is_not_empty(children):
                for c in children:
                    build_graph(graph, current_id, c, children[c])

        graph = nx.DiGraph()
        build_graph(graph, None, AggregationTree.root_id, self._doc.root)
        self.graph = graph

    def _sync_graph_to_doc(self):
        '''Converts internal tree to dict for CouchDB document'''
        assert self.graph is not None

        def build_dicts(dicts, parent, node_dict):
            for n in node_dict:
                # if we haven't seen it yet, build a dict for it
                if n not in dicts:
                    d = dict(self.graph.node[n])
                    dicts[n] = d  # hang onto them until they are connected up so don't get garbage collected!
                else:
                    d = dicts[n]

                # add to parent
                if parent is not None:
                    parent['_children'][n] = d

                # recurse children
                children = node_dict[n]
                if is_not_empty(children):
                    if '_children' not in d:
                        d['_children'] = dict()
                    build_dicts(dicts, d, node_dict[n])

        # walk the tree and pull out dicts and values and construct
        # dict for couchdb, save the root!
        seen = {}
        build_dicts(seen, None, self.graph.adj)
        self._doc.root = seen[AggregationTree.root_id]
