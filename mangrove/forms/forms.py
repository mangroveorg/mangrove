from collections import OrderedDict
from copy import deepcopy

from mangrove.errors.MangroveException import FormModelDoesNotExistsException
from mangrove.datastore.database import DatabaseManager
from mangrove.forms.documents import FormDocument
from mangrove.forms.fields import Field
from mangrove.utils.types import is_string

def form_by_code(dbm, code):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(code)
    rows = dbm.load_all_rows_in_view('form_by_code', key=code)
    if not len(rows):
        raise FormModelDoesNotExistsException(code)

    rows[0]['value'].pop('_rev')
    form = Form.build_from_dct(rows[0]['value'])
    return form

def _get_declared_fields(bases, attrs):
    fields = [(field_name, attrs.pop(field_name)) for field_name, obj in attrs.items() if isinstance(obj, Field)]
    fields.sort(key = lambda x: x[1].creation_counter)

    for base in bases[::-1]:
        if hasattr(base, 'base_fields'):
            fields = base.base_fields.items() + fields

    return OrderedDict(fields)

def _get_meta_class_properties(attrs):
    properties = {property_name: attrs.pop(property_name) for property_name, value in attrs.items() if not property_name.startswith("__")}
    return properties

class MangroveFormMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = _get_declared_fields(bases, attrs)
        attrs['uuid'] = None
        if attrs.get('Meta'):
            attrs['_metadata'] = _get_meta_class_properties(attrs.get('Meta').__dict__)
            def function(self): return value
            for key, value in attrs['_metadata'].items():
                if not key.startswith('__'): attrs[key] = function
            attrs['Meta'] = type('Meta', (), attrs['_metadata'])

        return super(MangroveFormMetaclass,
                     cls).__new__(cls, name, bases, attrs)

class BaseForm(object):

    def __init__(self, data=None):
        self.is_bound = data is not None
        self.data = data or {}
        self.fields = deepcopy(self.base_fields)

    def _errors(self):
        _errors = []
        _cleaned_data = []
        for name, field in self.fields.items():
            errors, value = field.validate(self.data.get(name))
            if (not errors) and (not value) and (not field.required): continue
            _errors.append((name, errors)) if errors else _cleaned_data.append((name, value))
        
        if not _errors:
            setattr(self, 'cleaned_data', OrderedDict(_cleaned_data))
        else:
            setattr(self, 'errors', OrderedDict(_errors))
        return OrderedDict(_errors)

    def is_valid(self):
        return self.is_bound and not bool(self._errors())

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
        dct['uuid'] = dct.pop('_id') if '_id' in dct.keys() else None
        dct['code'] = dct.pop('code')
        fields = dct.pop('fields') if dct.get('fields') else {}
        metadata = dct.pop('metadata') if dct.get('metadata') else {}
        field_classes = []
        for field_name, field_json in fields.items():
            field = Field.build_from_dct(field_json)
            field_classes.append((field_name, field))
        dct['base_fields'] = OrderedDict(field_classes)
        dct['_metadata'] = metadata
        for key, value in metadata.items():
            dct[key] = create_meta_functions(value)
        dct['Meta'] = type('Meta', (), metadata)
        return type('Form', (BaseForm,), dct)


def create_meta_functions(value):
    def func(self):
        return value

    return func
