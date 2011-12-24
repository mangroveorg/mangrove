# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from collections import OrderedDict
from mangrove.utils.types import is_empty
EMPTY_VALUES = (None, '', [], (), {})

def case_insensitive_lookup(values, code):
    for fieldcode in values:
        if fieldcode.lower() == code.lower():
            return values[fieldcode]
    return None

class MandatoryValidator(object):

    def get_mandatory_fields(self, fields):
        return [field for field in fields if field.is_required()]


    def validate(self,values,fields):
        errors = OrderedDict()
        mandatory_fields = self.get_mandatory_fields(fields)
        for field in mandatory_fields:
            if is_empty(case_insensitive_lookup(values, field.code)):
                errors[field.code] = "Answer for question " + str(field.code) + " is required"
        return errors

class MobileNumberMandatoryForReporterRegistrationValidator(object):

    def validate(self, values, fields):
        from mangrove.form_model.form_model import REPORTER, MOBILE_NUMBER_FIELD_CODE, ENTITY_TYPE_FIELD_CODE

        field_code = [field.code for field in fields if field.code == MOBILE_NUMBER_FIELD_CODE][0]
        if case_insensitive_lookup(values, ENTITY_TYPE_FIELD_CODE) == REPORTER and is_empty(case_insensitive_lookup(values, MOBILE_NUMBER_FIELD_CODE)):
            return OrderedDict({str(field_code):'Mobile number is missing'})
        return OrderedDict({})
