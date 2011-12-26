from mangrove.forms.validators import TelephoneNumberValidator
from mangrove.forms.validators import GeoCodeValidator
from mangrove.forms.validators import SequenceValidator
from mangrove.forms import validators
from mangrove.utils.types import is_empty

class Field(object):

    creation_counter = 0
    default_validator_messages = {
        'required': "This field is required.",
        'invalid': "Enter a valid value",
    }
    def __init__(self, code, label, validators, instruction, required):
        self.code = code
        self.label = label
        self.validators = validators
        self.instruction = instruction
        self.required = required
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

    def validate(self, value):
        errors = []
        if is_empty(value) and self.required:
            return [self.default_validator_messages['required']], value
        for validator in self.validators:
            try:
                value =validator.validate(value)
            except Exception as ex:
                errors.append(ex.message)

        return errors, value

    def to_json(self):
        validators_json = []
        for validator in self.validators:
            validators_json.append(validator._to_json())
        return {'_class': self.__class__.__name__,
                'code': self.code,
                'label': self.label,
                'required': self.required,
                'instruction': self.instruction,
                'validators': validators_json}


    @classmethod
    def build_from_dct(cls, dct):
        field_class_name = dct.pop('_class')
        dct['validators'] = validators.validator_factory(dct.get('validators') or [])
        field = type(field_class_name, (eval(field_class_name),Field,), {})(**dct)
        return field

class TextField(Field):
    
    default_constraints = []

    def __init__(self, code, label, validators=default_constraints, instruction="", default="", required=False):
        Field.__init__(self, code, label, validators, instruction, required)
        self.default = default
        self.required = required

    def to_json(self):
        _json = Field.to_json(self)
        _json['default'] = self.default
        return _json

class HierarchyField(Field):
    default_constraints = []
    def __init__(self, code, label, validators=default_constraints, instruction=None,required=False):
        Field.__init__(self, code=code, label=label, instruction=instruction,required=required, validators=validators)

    def validate(self, value):
        errors = []
        if is_empty(value):
            if self.required:
                return list(self.default_validator_messages['required']), value
            else:
                return [], value
        try:
            value = SequenceValidator().validate(value)
        except Exception as ex:
            errors.append(ex.message)
        return errors, value

class GeoCodeField(Field):
    default_validators = []
    def __init__(self, code, label, instruction="",required=False, validators=default_validators):
        Field.__init__(self, code=code,
                       label=label, instruction=instruction,required=required, validators=validators)

    def validate(self, value):
        if is_empty(value):
            value = ""
        errors, value = Field.validate(self,value)
        try:
            value = GeoCodeValidator().validate(value)
        except Exception as ex:
            errors.append(ex.message)
        return errors, value

class TelephoneNumberField(Field):
    default_validators = []
    def __init__(self, code, label, instruction="", required=False, validators=default_validators):
        Field.__init__(self, code=code, label=label,
                           instruction=instruction, validators=validators, required=required)

    def validate(self, value):
        value = TelephoneNumberValidator().validate(value)
        return Field.validate(self, value)

