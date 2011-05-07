# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from threading import Lock

import networkx as nx

from mangrove.utils.types import is_not_empty
from documents import AggregationTreeDocument
from database import DatabaseManager


class AggregationTree(object):
    '''
    Representation of an aggregation tree.

    In memory this utilizes the NetworkX graph library with each node being a dict

    The tree is represented in Couch as dicts of dicts under the attribute '_root'

    Each tree has a unique _id and an expected unique _name.


    Each node in the tree is a dict of arbitrary attributes, a _unique_ '_id' attribute
    and a special '_children' attribute that holds the child nodes.

    So a tree with a partial list of countries and states/provinces of this form (in pseudo-lisp-code):

    ((India(Maharashtra, Kerala, Karnataka)), (US(California(SF), Ohio)))



    would look like this

    {
    _id: 123445435
    _name: _geo
    _root: {
            children: {
                         { id: India, children: [{ id: Maharashtra}, { id: Kerala}, {id: Karnataka}]},
                         { id: US, children: [{ id: California, _children: [{id: SF}]}, {id: Ohio}]},
                      }
            }
    }


    '''
    root_id = '__root'

    def __init__(self, dbm, name, _document=None):
        '''
        Note: _document is for 'protected' factory methods. If it is passed in the other
        arguments are ignored.

        '''
        assert isinstance(dbm, DatabaseManager)
        assert ((_document is None and is_not_empty(name)) or
               (_document is not None and isinstance(_document, AggregationTreeDocument)))

        self._dbm = dbm
        self.graph = None

        if _document is not None:
            self._doc = _document
        else:
            self._doc = AggregationTreeDocument(name)

        self._sync_doc_to_graph()

    def save(self):
        id = None
        with Lock():
            self._sync_graph_to_doc()
            id = self._dbm.save(self._doc).id
        return id

    @property
    def name(self):
        return self._doc.name

    @name.setter
    def name(self, value):
        self._doc.name = value

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
                    build_graph(graph, current_id, c)

        graph = nx.DiGraph()
        build_graph(graph, None, AggregationTree.root_id, self._doc.root)
        self.graph = graph

    def _sync_graph_to_doc(self):
        '''Converts internal tree to dict for CouchDB document'''

        assert self.graph is not None

        def build_dicts(dicts, parent, node_dict):
            for n in node_dict:
                # if we haven't seen it yet, build a dict for it
                d = None
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
