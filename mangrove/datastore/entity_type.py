

""" Module to deal with entity types.
for example Clinic, Hospital, Waterpoints, School etc are entity types
"""

from mangrove.datastore.aggregationtree import AggregationTree
from mangrove.datastore.database import DatabaseManager
from mangrove.errors.MangroveException import EntityTypeAlreadyDefined
from mangrove.utils.types import is_not_empty, is_sequence

ENTITY_TYPE_TREE_ID = u'entity_type_tree'

def define_type(dbm, entity_type):
    """
    Add this entity type to the tree of all entity types and save it
    to the database. entity_type may be a string or a list of
    strings.
    """
    assert is_not_empty(entity_type)
    assert is_sequence(entity_type)
    assert isinstance(dbm, DatabaseManager)
    if entity_type_already_defined(dbm, entity_type):
        raise EntityTypeAlreadyDefined(u"Type: %s is already defined" % u'.'.join(entity_type))
    entity_tree = AggregationTree.get(dbm, ENTITY_TYPE_TREE_ID, get_or_create=True)
    entity_tree.add_path([AggregationTree.root_id] + entity_type)
    entity_tree.save()

def get_all_entity_types(dbm):
    """
    Return a list of all entity types. If we think of all entity types
    organized in a hierarchical tree, an entity type is a node in this
    tree and the node is represented by a list containing the node
    names in the path to this node.
    """
    return AggregationTree.get(dbm, ENTITY_TYPE_TREE_ID, get_or_create=True).get_paths()

def get_unique_id_types(manager):
    entity_types = get_all_entity_types(manager)
    return sorted([entity_type[0] for entity_type in entity_types if entity_type[0] != 'reporter'])

def delete_type(dbm, entity):
    assert isinstance(dbm, DatabaseManager)
    entity_tree = AggregationTree.get(dbm, ENTITY_TYPE_TREE_ID, get_or_create=True)
    for entity_item in entity:
        entity_tree.remove_node(entity_item)
        entity_tree.save()

def entity_type_already_defined(dbm, entity_type):
    """
    Return True if entity_type is already defined else false
    """
    type_path = [item.strip() for item in entity_type]
    all_entities = get_all_entity_types(dbm)
    if all_entities:
        all_entities_lower_case = [[x.lower() for x in each] for each in all_entities]
        entity_type_lower_case = [each.lower() for each in type_path]
        if entity_type_lower_case in all_entities_lower_case:
            return True
    return False

