
class Field(object):

    default_constraints = {
        'required': "This field is required.",
        'invalid': "Enter a valid value",
    }
    def __init__(self, name, code, label, constraints, instruction):
        self.name = name
        self.code = code
        self.label = label
        self.constraints = constraints
        self.instruction = instruction

    def validate(self):
        pass

class TextField(Field):
    
    default_constraints = []

    def __init__(self, name, code, label, constraints=default_constraints, instruction=None, default=""):
        Field.__init__(self, name, code, label, constraints, instruction)
        self.value = default

    def to_json(self):
        return {'name': self.name,
                'code': self.code,
                'label': self.label}
