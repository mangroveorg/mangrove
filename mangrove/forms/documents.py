from collections import OrderedDict
from couchdb.mapping import DictField, TextField, BooleanField, ListField, Mapping
from mangrove.datastore.documents import DocumentBase

class FormDocument(DocumentBase):
    code = TextField()
    fields = DictField()
    metadata = DictField()
    
    def __init__(self, **args):
        DocumentBase.__init__(self, args.get('_id'), document_type='FormModel')
        self.code = args.get('code') or ""
        self.fields = args.get('fields') or {}
        if args.get('metadata'):
            self.metadata = args.get('metadata')

    @classmethod
    def save(cls, form, dbm):
        fields_dct = {}
        for name, field in form.fields.items():
            fields_dct[name] = field.to_json()
        dct = {
            '_id': form.uuid,
            'fields': fields_dct,
            'code': form.code,
            'metadata': form._metadata if hasattr(form, '_metadata') else {}
        }

        document = cls(**dct)
        return document.store(dbm.database).id

