from mangrove.forms import validators

class Field(object):

    default_constraints_message = {
        'required': "This field is required.",
        'invalid': "Enter a valid value",
    }
    def __init__(self, name, code, label, constraints, instruction, required):
        self.name = name
        self.code = code
        self.label = label
        self.constraints = constraints
        self.instruction = instruction
        self.required = required

    def validate(self, value):
        if value in validators.EMPTY_VALUES and self.required:
            return [self.default_constraints_message['required']]
        return []


class TextField(Field):
    
    default_constraints = []

    def __init__(self, name, code, label, constraints=default_constraints, instruction=None, default="", required=False):
        Field.__init__(self, name, code, label, constraints, instruction, required)
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
        for constraint in self.constraints:
            try:
                constraint.validate(value)
            except Exception as ex:
                errors.append(ex.message)
        return errors