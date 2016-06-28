import uuid

from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import EntityPreferenceDocument


def get_entity_preference(manager, org_id, entity_type):
    rows = manager.load_all_rows_in_view('entity_preference', key=[org_id, entity_type])
    entity_preference = None
    if len(rows):
        entity_preference = EntityPreference.new_from_doc(manager, EntityPreferenceDocument.wrap(rows[0]['value']))
    return entity_preference


def save_entity_preference(manager, org_id, entity_type):
    entity_preference = get_entity_preference(manager, org_id, entity_type)
    if entity_preference is None:
        entity_preference = EntityPreference(manager, org_id, entity_type, uuid.uuid1())
    entity_preference.save()
    return entity_preference


class EntityPreference(DataObject):
    __document_class__ = EntityPreferenceDocument

    def __init__(self, dbm, org_id=None, entity_type=None, share_token=None, **kwargs):
        super(EntityPreference, self).__init__(dbm)
        doc = EntityPreferenceDocument()
        doc.org_id = org_id
        doc.entity_type = entity_type
        doc.share_token = share_token
        DataObject._set_document(self, doc)

    @property
    def share_token(self):
        return self._doc.share_token
