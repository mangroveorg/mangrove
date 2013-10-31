# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.contrib.delete_validators import EntityShouldExistValidator
from mangrove.form_model.validator_types import ValidatorTypes
from mangrove.form_model.validators import MandatoryValidator

def validator_factory(validator_json):
    validator_class = validators.get(validator_json['cls'])
    return validator_class()


validators = {
    ValidatorTypes.MANDATORY : MandatoryValidator,
    ValidatorTypes.ENTITY_SHOULD_EXIST : EntityShouldExistValidator,
    }