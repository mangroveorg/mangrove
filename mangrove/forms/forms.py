from collections import OrderedDict
from copy import deepcopy
from mangrove.forms.documents import FormDocument

from mangrove.forms.fields import Field

def get_declared_fields(bases, attrs):
    fields = [(obj.name, attrs.pop(field_name)) for field_name, obj in attrs.items() if isinstance(obj, Field)]

    for base in bases[::-1]:
        if hasattr(base, 'base_fields'):
            fields = base.base_fields.items() + fields

    return OrderedDict(fields)

class MangroveFormMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = get_declared_fields(bases, attrs)
        if attrs.get('Meta'):
            def function(self): return value
            for key, value in attrs.get('Meta').__dict__.items():
                if not key.startswith('__'): attrs[key] = function

        return super(MangroveFormMetaclass,
                     cls).__new__(cls, name, bases, attrs)

class BaseForm(object):

    def __init__(self, data=None):
        self.is_bound = data is not None
        self.data = data or {}
        self.fields = deepcopy(self.base_fields)

    @property
    def errors(self):
        _errors = []
        for field in self.fields.values():
            error = field.validate(self.data.get(field.name))
            if error:
                _errors.append((field.name, error))
        return _errors

    def is_valid(self):
        return self.is_bound and not bool(self.errors)

    def __getitem__(self, name):
        field = self.fields[name]
        return field

    def save(self, dbm):
        id = FormDocument.save(self, dbm)
        setattr(self, 'uuid', id)
        return self

class Form(BaseForm):
    __metaclass__ = MangroveFormMetaclass

    @classmethod
    def build_from_dct(cls, dct):
        fields = dct.pop('fields') if dct.get('fields') else []
        metadata = dct.pop('metadata') if dct.get('metadata') else {}
        field_classes = []
        for field_json in fields:
            field = Field.build_from_dct(field_json)
            field_classes.append((field.name, field))
        dct['base_fields'] = OrderedDict(field_classes)
        for key, value in metadata.items():
            def func(self): return value
            dct[key] = func
        return type('Form', (BaseForm,), dct)
