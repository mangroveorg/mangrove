from couchdb.mapping import TextField, FloatField, BooleanField
from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import DocumentBase


class MediaDocument(DocumentBase):
    name = TextField()
    size = FloatField()
    questionnaire_id = TextField()
    is_preview = BooleanField()

    def __init__(self, id=None, attachment_name=None, attachment_size=None, questionnaire_id=None, is_preview=False):
        DocumentBase.__init__(self, id=id, document_type='MediaDetails')
        self.name = attachment_name
        self.size = attachment_size
        self.questionnaire_id = questionnaire_id
        self.is_preview = is_preview


class Media(DataObject):
    __document_class__ = MediaDocument

    def __init__(self, dbm, attachment_name=None, attachment_size=None, questionnaire_id=None, is_preview=False):
        DataObject.__init__(self, dbm)
        doc = MediaDocument(attachment_name=attachment_name, attachment_size=attachment_size, questionnaire_id=questionnaire_id, is_preview=is_preview)
        DataObject._set_document(self, doc)
