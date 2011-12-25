from couchdb.mapping import DictField, TextField, BooleanField, ListField, Mapping
from mangrove.datastore.documents import DocumentBase

class FormDocument(DocumentBase):
    name = TextField()
    form_code = TextField()
    state = TextField()
    json_fields = ListField(DictField())
    metadata = DictField()
    
    def __init__(self, **args):
        DocumentBase.__init__(self, args.get('_id'), document_type='FormModel')
        self.name = args.get('name') or ""
        self.form_code = args.get('code') or ""
        self.state = args.get('state') or ""
        self.json_fields = args.get('json_fields') or []
        if args.get('metadata'):
            self.metadata = args.get('metadata')

    @classmethod
    def save(cls, form, dbm):
        fields_dct = []
        for field in form.fields.values():
            fields_dct.append(field.to_json())
        dct = {
            '_id': form.uuid if hasattr(form, 'uuid') else None,
            'name': form.name,
            'state': form.state,
            'json_fields': fields_dct,
            'code': form.code
        }

        document = cls(**dct)
        return document.store(dbm.database).id

