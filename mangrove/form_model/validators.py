from collections import OrderedDict
from mangrove.errors.MangroveException import DataObjectNotFound
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.utils.types import is_empty
from mangrove.datastore.entity import get_by_short_code
from mangrove.form_model.field import field_attributes

def case_insensitive_lookup(values, code):
    for fieldcode in values:
        if fieldcode.lower() == code.lower():
            return values[fieldcode]
    return None


class MandatoryValidator(object):
    def get_mandatory_fields(self, fields):
        return [field for field in fields if field.is_required()]


    def validate(self, values, fields, dbm=None):
        errors = OrderedDict()
        mandatory_fields = self.get_mandatory_fields(fields)
        for field in mandatory_fields:
            if is_empty(case_insensitive_lookup(values, field.code)):
                errors[field.code] = "Answer for question %s is required." % str(field.code)
        return errors

    def to_json(self):
        return dict(cls=ValidatorTypes.MANDATORY)

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return True
        return False


class UniqueIdExistsValidator(object):
    def get_unique_id_field(self, fields):
        return [field for field in fields if field.type == field_attributes.UNIQUE_ID_FIELD]


    def validate(self, values, fields, dbm=None):
        errors = OrderedDict()
        unique_id_fields = self.get_unique_id_field(fields)
        for field in unique_id_fields:
            unique_id = case_insensitive_lookup(values, field.code)
            try:
                get_by_short_code(dbm, unique_id, [field.unique_id_type])
            except DataObjectNotFound as e:
                errors[field.code] = e.message
        return errors

    def to_json(self):
        return dict(cls=ValidatorTypes.UNIQUE_ID_EXISTS)

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return True
        return False
