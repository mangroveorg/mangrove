# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from collections import OrderedDict
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.utils.types import is_empty

class AtLeastOneLocationFieldMustBeAnsweredValidator(object):
    def validate(self, values, fields):
        from mangrove.form_model.form_model import GEO_CODE, LOCATION_TYPE_FIELD_CODE

        if is_empty(case_insensitive_lookup(values, GEO_CODE)) and is_empty(
            case_insensitive_lookup(values, LOCATION_TYPE_FIELD_CODE)):
            errors = OrderedDict()
            errors[GEO_CODE] = 'Please fill out at least one location field correctly.'
            errors[LOCATION_TYPE_FIELD_CODE] = 'Please fill out at least one location field correctly.'
            return errors
        return OrderedDict()

    def to_json(self):
        return {'cls': ValidatorTypes.At_Least_One_Location_Field_Must_Be_Answered}

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return True
        return False

class MobileNumberValidationsForReporterRegistrationValidator(object):

    def validate(self, values, fields):
        from mangrove.form_model.form_model import REPORTER, MOBILE_NUMBER_FIELD_CODE, ENTITY_TYPE_FIELD_CODE

        field_code = [field.code for field in fields if field.code == MOBILE_NUMBER_FIELD_CODE][0]
        if case_insensitive_lookup(values, ENTITY_TYPE_FIELD_CODE) == REPORTER and is_empty(case_insensitive_lookup(values, MOBILE_NUMBER_FIELD_CODE)):
            return OrderedDict({str(field_code):'Mobile number is missing'})
        return OrderedDict({})

    def to_json(self):
        return dict(cls=ValidatorTypes.MOBILE_NUMBER_MANDATORY_FOR_REPORTER)

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return True
        return False

def case_insensitive_lookup(values, code):
    for fieldcode in values:
        if fieldcode.lower() == code.lower():
            return values[fieldcode]
    return None
