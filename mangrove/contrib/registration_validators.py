# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from collections import OrderedDict
import re
from mangrove.data_cleaner import TelephoneNumber
from mangrove.errors.MangroveException import NumberNotRegisteredException
from mangrove.errors.error_codes import EMAIL_NOT_UNIQUE, INVALID_EMAIL, EMPTY_MOBILE_NUMBER, DUPLICATE_MOBILE_NUMBER, MANDATORY_FIELD_REQUIRED, ATLEAST_SINGLE_LOCATION_ENTRY_SHOULD_BE_PRESENT
from mangrove.errors.errors import Error
from mangrove.form_model.field import email_regex
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.form_model.validators import MandatoryValidator
from mangrove.utils.types import is_empty


class AtLeastOneLocationFieldMustBeAnsweredValidator(object):
    def validate(self, values, fields=None, dbm=None):
        from mangrove.form_model.form_model import GEO_CODE, LOCATION_TYPE_FIELD_CODE, LOCATION_TYPE_FIELD_NAME, GEO_CODE_FIELD_NAME

        errors = []
        if is_empty(case_insensitive_lookup(values, GEO_CODE)) and is_empty(
                case_insensitive_lookup(values, LOCATION_TYPE_FIELD_CODE)):
            errors.append(Error(LOCATION_TYPE_FIELD_NAME, ATLEAST_SINGLE_LOCATION_ENTRY_SHOULD_BE_PRESENT))
            errors.append(Error(GEO_CODE_FIELD_NAME, ATLEAST_SINGLE_LOCATION_ENTRY_SHOULD_BE_PRESENT))
        return errors

    def to_json(self):
        return {'cls': ValidatorTypes.At_Least_One_Location_Field_Must_Be_Answered}

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return True
        return False


class MobileNumberValidationsForReporter():
    def validate(self, values, fields, dbm):
        from mangrove.form_model.form_model import REPORTER, MOBILE_NUMBER_FIELD_CODE, ENTITY_TYPE_FIELD_CODE, SHORT_CODE

        errors = []
        field_name = [field.name for field in fields if field.code == MOBILE_NUMBER_FIELD_CODE][0]

        if case_insensitive_lookup(values, ENTITY_TYPE_FIELD_CODE) == REPORTER:
            phone_number = case_insensitive_lookup(values, MOBILE_NUMBER_FIELD_CODE)
            if is_empty(phone_number):
                errors.append(Error(field_name, EMPTY_MOBILE_NUMBER))
            elif not self._is_phone_number_unique(dbm, phone_number, case_insensitive_lookup(values, SHORT_CODE)):
                errors.append(Error(field_name, DUPLICATE_MOBILE_NUMBER, value=phone_number))

        return errors

    def to_json(self):
        return dict(cls=ValidatorTypes.MOBILE_NUMBER_MANDATORY_FOR_REPORTER)

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return True
        return False

    def _is_phone_number_unique(self, dbm, phone_number, reporter_id):
        from mangrove.transport.repository.reporters import find_reporters_by_from_number
        try:
            registered_reporters = find_reporters_by_from_number(dbm, self._clean(phone_number))
        except NumberNotRegisteredException:
            return True
        if len(registered_reporters) == 1 and registered_reporters[0].short_code == reporter_id:
            return True
        return False

    def _clean(self, value):
        return TelephoneNumber().clean(value)


class EmailFieldValidatorForReporter():
    def validate(self, values, fields, dbm):
        from mangrove.form_model.form_model import EMAIL_FIELD_CODE

        errors = []
        field_name = [field.name for field in fields if field.code == EMAIL_FIELD_CODE][0]

        email = case_insensitive_lookup(values, EMAIL_FIELD_CODE)
        if is_empty(email):
            return errors
        if not re.match(email_regex, email):
            errors.append(Error(field_name, INVALID_EMAIL, email))
            return errors
        if not self._is_email_unique(dbm, email):
            errors.append(Error(field_name, EMAIL_NOT_UNIQUE, email))
        return errors

    def to_json(self):
        return dict(cls=ValidatorTypes.EMAIL_FIELD_VALIDATOR_FOR_REPORTER)

    def _is_email_unique(self, dbm, email):
        reporters_with_matching_email = dbm.view.datasender_by_email(key=email, include_docs=False)
        if reporters_with_matching_email:
            return False
        return True

class MandatoryValidatorForReporter():
    def get_mandatory_fields(self, fields):
        return [field for field in fields if field.is_required()]

    def to_json(self):
        return dict(cls=ValidatorTypes.MANDATORY_FIELD_FOR_REPORTER)

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return True
        return False

    def validate(self,values,fields, dbm=None):
        errors = []
        mandatory_fields = self.get_mandatory_fields(fields)
        for field in mandatory_fields:
            if is_empty(case_insensitive_lookup(values, field.code)):
                errors.append(Error(field.name,MANDATORY_FIELD_REQUIRED))
        return errors


def case_insensitive_lookup(values, code):
    for fieldcode in values:
        if fieldcode.lower() == code.lower():
            return values[fieldcode]
    return None
