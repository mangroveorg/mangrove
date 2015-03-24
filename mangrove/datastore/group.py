from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import GroupDocument
from mangrove.utils.types import is_string


class Group(DataObject):
    __document_class__ = GroupDocument

    def __init__(self, dbm, name):
        super(Group, self).__init__(dbm)
        assert is_string(name)
        doc = GroupDocument()
        doc.name = name
        DataObject._set_document(self, doc)