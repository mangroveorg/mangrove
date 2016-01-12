
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Contact
from mangrove.utils.types import is_string

def get_entity_count_for_type(dbm, entity_type):
    if is_string(entity_type):
        entity_type = [entity_type]
    rows = dbm.view.count_entities_by_type(key=entity_type)
    return rows[0][u"value"] if len(rows) else 0

def get_non_voided_entity_count_for_type(dbm, entity_type):
    if is_string(entity_type):
        entity_type = [entity_type]
    rows = dbm.view.count_non_voided_entities_by_type(key=entity_type)
    return rows[0][u"value"] if len(rows) else 0

def get_all_by_type(dbm, entity_type):
    rows = dbm.view.by_type(key=entity_type,include_docs=True)
    return [row['doc'] for row in rows]

def get_all_reporters(dbm):
    """
    Return a list of all entities with this type.
    """
    # TODO: change this?  for now it assumes _type is
    # non-heirarchical. Might also benefit from using get_many.
    assert isinstance(dbm, DatabaseManager)

    rows = dbm.view.by_type(key="reporter", include_docs=True)
    return [_get_contact_from_json(dbm, row['doc']) for row in rows]

def _get_contact_from_json(dbm ,doc):
    return Contact.new_from_doc(dbm, Contact.__document_class__.wrap(doc))
