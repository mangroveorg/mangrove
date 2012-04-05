# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from collections import OrderedDict
from mangrove.datastore.entity import entities_exists_with_value
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.utils.types import is_empty

class AtLeastOneLocationFieldMustBeAnsweredValidator(object):
    def validate(self, values, fields=None, dbm=None):
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

    def validate(self, values, fields, dbm, registered_phone_numbers=[]):
        from mangrove.form_model.form_model import REPORTER, MOBILE_NUMBER_FIELD_CODE, ENTITY_TYPE_FIELD_CODE, MOBILE_NUMBER_FIELD

        errors = OrderedDict()
        field_code = [field.code for field in fields if field.code == MOBILE_NUMBER_FIELD_CODE][0]

        if case_insensitive_lookup(values, ENTITY_TYPE_FIELD_CODE) == REPORTER:
            phone_number = case_insensitive_lookup(values, MOBILE_NUMBER_FIELD_CODE)
            if is_empty(phone_number):
               errors[field_code] = u'Mobile number is missing'
            elif phone_number in registered_phone_numbers or\
                 entities_exists_with_value(dbm, [REPORTER], MOBILE_NUMBER_FIELD, phone_number):
                errors[MOBILE_NUMBER_FIELD_CODE] = u'Sorry, the telephone number %s has already been registered' % (phone_number,)

        return errors

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
