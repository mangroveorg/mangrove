from couchdb.mapping import TextField, FloatField
from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import DocumentBase


class MediaDocument(DocumentBase):
    name = TextField()
    size = FloatField()
    questionnaire_id = TextField()

    def __init__(self, id=None, attachment_name=None, attachment_size=None, questionnaire_id=None):
        DocumentBase.__init__(self, id=id, document_type='MediaDetails')
        self.name = attachment_name
        self.size = attachment_size
        self.questionnaire_id = questionnaire_id


class Media(DataObject):
    __document_class__ = MediaDocument

    def __init__(self, dbm, attachment_name=None, attachment_size=None, questionnaire_id=None):
        DataObject.__init__(self, dbm)
        doc = MediaDocument(attachment_name=attachment_name, attachment_size=attachment_size, questionnaire_id=questionnaire_id)
        DataObject._set_document(self, doc)
