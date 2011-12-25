from mangrove.forms.validators import validator_factory
from mangrove.forms import validators

class Field(object):

    default_validator_messages = {
        'required': "This field is required.",
        'invalid': "Enter a valid value",
    }
    def __init__(self, name, code, label, validators, instruction, required):
        self.name = name
        self.code = code
        self.label = label
        self.validators = validators
        self.instruction = instruction
        self.required = required

    def validate(self, value):
        if value in validators.EMPTY_VALUES and self.required:
            return [self.default_validator_messages['required']]
        return []

    @classmethod
    def build_from_dct(cls, dct):
        field_class_name = dct.pop('_class')
        dct['validators'] = validator_factory(dct.get('validators') or [])
        field = type(field_class_name, (eval(field_class_name),Field,), {})(**dct)
        return field

class TextField(Field):
    
    default_constraints = []

    def __init__(self, name, code, label, validators=default_constraints, instruction=None, default="", required=False):
        Field.__init__(self, name, code, label, validators, instruction, required)
        self.default = default
        self.required = required

    def to_json(self):
        return {'_class': 'TextField',
                'name': self.name,
                'code': self.code,
                'label': self.label,
                'default':self.default,
                'required': self.required}

    def validate(self, value):
        errors = Field.validate(self,value)
        for validators in self.validators:
            try:
                validators.validate(value)
            except Exception as ex:
                errors.append(ex.message)
        return errors