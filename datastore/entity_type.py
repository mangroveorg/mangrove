# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Module to deal with entity types.
for example Clinic, Hospital, Waterpoints, School etc are entity types
"""

import mangrove.datastore.aggregationtree as atree
from mangrove.datastore.database import DatabaseManager, DataObject
from mangrove.errors.MangroveException import EntityTypeAlreadyDefined
from mangrove.utils.types import is_not_empty, is_sequence, is_string

ENTITY_TYPE_TREE = u'entity_type_tree'

def define_type(dbm, entity_type):
    """
    Add this entity type to the tree of all entity types and save it
    to the database. entity_type may be a string or a list of
    strings.
    """
    assert is_not_empty(entity_type)
    assert is_sequence(entity_type)
    type_path = [item.strip() for item in entity_type]
    if entity_type_already_defined(dbm, type_path):
        raise EntityTypeAlreadyDefined(u"Type: %s is already defined" % u'.'.join(entity_type))
        # now make the new one
    entity_tree = _get_entity_type_tree(dbm)
    entity_tree.add_path([atree.AggregationTree.root_id] + entity_type)
    entity_tree.save()

def get_all_entity_types(dbm):
    """
    Return a list of all entity types. If we think of all entity types
    organized in a hierarchical tree, an entity type is a node in this
    tree and the node is represented by a list containing the node
    names in the path to this node.
    """
    return _get_entity_type_tree(dbm).get_paths()


def entity_type_already_defined(dbm, entity_type):
    """
    Return True if entity_type is already defined else false
    """
    all_entities = get_all_entity_types(dbm)
    if all_entities:
        all_entities_lower_case = [[x.lower() for x in each] for each in all_entities]
        entity_type_lower_case = [each.lower() for each in entity_type]
        if entity_type_lower_case in all_entities_lower_case:
            return True
    return False


def _get_entity_type_tree(dbm):
    """
    Return the AggregationTree object with id equal to
    'entity_type_tree'.
    """
    assert isinstance(dbm, DatabaseManager)
    return dbm.get(ENTITY_TYPE_TREE, atree.AggregationTree, get_or_create=True)

