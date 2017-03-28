import uuid

from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import EntityPreferenceDocument


def get_entity_preference(manager, org_id, entity_type):
    rows = manager.load_all_rows_in_view('entity_preference', key=[org_id, entity_type])
    if len(rows):
        return EntityPreference.new_from_doc(manager, EntityPreferenceDocument.wrap(rows[0]['value']))
    return None


def get_entity_preference_by_share_token(manager, share_token):
    rows = manager.load_all_rows_in_view('entity_preference_by_share_token', key=share_token)
    if len(rows):
       return EntityPreference.new_from_doc(manager, EntityPreferenceDocument.wrap(rows[0]['value']))
    return None


def save_entity_preference(manager, org_id, entity_type, filters=None, details=None, specials=None, fallback_location=None):
    entity_preference = get_entity_preference(manager, org_id, entity_type)

    if entity_preference is None:
        entity_preference = EntityPreference(manager, org_id, entity_type, uuid.uuid1())

    if filters is not None:
        entity_preference.set_filters(filters)

    if details is not None:
        entity_preference.set_details(details)

    if specials is not None:
        entity_preference.set_specials(specials)

    if fallback_location is not None:
        entity_preference.set_fallback_location(fallback_location)

    entity_preference.save()
    return entity_preference


class EntityPreference(DataObject):
    __document_class__ = EntityPreferenceDocument

    def __init__(self, dbm, org_id=None, entity_type=None, share_token=None, fallback_location=None, **kwargs):
        super(EntityPreference, self).__init__(dbm)
        doc = EntityPreferenceDocument()
        doc.org_id = org_id
        doc.entity_type = entity_type
        doc.share_token = share_token
        doc.fallback_location = fallback_location
        DataObject._set_document(self, doc)

    @property
    def share_token(self):
        return self._doc.share_token

    @property
    def entity_type(self):
        return self._doc.entity_type

    @property
    def org_id(self):
        return self._doc.org_id

    @property
    def filters(self):
        return self._doc.filters

    @property
    def details(self):
        return self._doc.details

    @property
    def specials(self):
        return self._doc.specials

    @property
    def fallback_location(self):
        return self._doc.fallback_location

    @property
    def total_in_label(self):
        return self._doc.total_in_label

    def set_filters(self, filters):
        self._doc.filters = filters

    def set_details(self, details):
        self._doc.details = details

    def set_specials(self, specials):
        self._doc.specials = specials

    def set_fallback_location(self, fallback_location):
        self._doc.fallback_location = fallback_location