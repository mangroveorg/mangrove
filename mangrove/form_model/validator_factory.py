
from mangrove.contrib.delete_validators import EntityShouldExistValidator
from mangrove.contrib.registration_validators import AtLeastOneLocationFieldMustBeAnsweredValidator, MobileNumberValidationsForReporterRegistrationValidator
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.form_model.validators import MandatoryValidator, UniqueIdExistsValidator


def validator_factory(validator_json):
    validator_class = validators.get(validator_json['cls'])
    return validator_class()


validators = {
    ValidatorTypes.MANDATORY : MandatoryValidator,
    ValidatorTypes.MOBILE_NUMBER_MANDATORY_FOR_REPORTER : MobileNumberValidationsForReporterRegistrationValidator,
    ValidatorTypes.At_Least_One_Location_Field_Must_Be_Answered : AtLeastOneLocationFieldMustBeAnsweredValidator,
    ValidatorTypes.ENTITY_SHOULD_EXIST : EntityShouldExistValidator,
    ValidatorTypes.UNIQUE_ID_EXISTS : UniqueIdExistsValidator,
    }