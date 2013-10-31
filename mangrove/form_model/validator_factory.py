# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.contrib.delete_validators import EntityShouldExistValidator
from mangrove.contrib.registration_validators import AtLeastOneLocationFieldMustBeAnsweredValidator, MobileNumberValidationsForReporter, EmailFieldValidatorForReporter, MandatoryValidatorForReporter
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.form_model.validators import MandatoryValidator

def validator_factory(validator_json):
    validator_class = validators.get(validator_json['cls'])
    return validator_class()


validators = {
    ValidatorTypes.MANDATORY : MandatoryValidator,
    ValidatorTypes.MANDATORY_FIELD_FOR_REPORTER: MandatoryValidatorForReporter,
    ValidatorTypes.MOBILE_NUMBER_MANDATORY_FOR_REPORTER : MobileNumberValidationsForReporter,
    ValidatorTypes.EMAIL_FIELD_VALIDATOR_FOR_REPORTER: EmailFieldValidatorForReporter,
    ValidatorTypes.At_Least_One_Location_Field_Must_Be_Answered : AtLeastOneLocationFieldMustBeAnsweredValidator,
    ValidatorTypes.ENTITY_SHOULD_EXIST : EntityShouldExistValidator,
    }