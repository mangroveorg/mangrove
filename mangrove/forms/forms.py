from collections import OrderedDict
from copy import deepcopy

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

class Form(BaseForm):
    __metaclass__ = MangroveFormMetaclass

    @classmethod
    def build_from_dct(cls, dct):
        attrs = {'code': dct['code']}
        fields = []
        for field_json in dct['fields']:
            field = Field.build_from_dct(field_json)
            fields.append((field.name, field))
        attrs['base_fields'] = OrderedDict(fields)
        return type('Form', (BaseForm,), attrs)



