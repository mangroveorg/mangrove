from errors.MangroveException import AnswerTooLongException, AnswerTooShortException
from mangrove.utils.types import is_empty
from validate import VdtValueTooLongError, VdtValueTooShortError

class Field(object):
    def __init__(self, type="", name="", code="", label='', instruction='', constraints=None,required=True):
        if not constraints: constraints = []
        self._dict = {}
        self._dict = {'name': name, 'type': type, 'code': code, 'instruction': instruction,'required':required, 'label': label}
        self.constraints = constraints
        self.errors = []
        self.value = None
        if not is_empty(constraints):
            self._dict['constraints'] = []
            for constraint in constraints:
                constraint_json = constraint._to_json()
                if not is_empty(constraint_json):
                    self._dict['constraints'].append(constraint_json)

    @property
    def name(self):
        return self._dict.get("name")

    @property
    def label(self):
        return self._dict.get('label')

    @property
    def type(self):
        return self._dict.get('type')

    @property
    def code(self):
        return self._dict.get('code')

    @property
    def instruction(self):
        return self._dict.get('instruction')

    @property
    def is_entity_field(self):
        return False


    def _to_json(self):
        dict = self._dict.copy()
        dict['instruction'] = self._dict['instruction']
        return dict

    def _to_json_view(self):
        json = self._to_json()

        if 'constraints' in json:
            constraints = json.pop('constraints')
            for constraint in constraints:
                json[constraint[0]] = constraint[1]
        return json

    def add_or_edit_label(self, label):
        self._dict['label'] = label

    def set_value(self, value):
        self.value = value

    def get_constraint_text(self):
        return ""

    def is_required(self):
        return self._dict['required']

class TextField(Field):
    DEFAULT_VALUE = "defaultValue"
    CONSTRAINTS = "constraints"
    ENTITY_QUESTION_FLAG = 'entity_question_flag'

    def __init__(self, name, code, label, constraints=None, defaultValue="", instruction=None):
        if not constraints: constraints = []
        assert isinstance(constraints, list)
        Field.__init__(self, name=name, code=code,
                       label=label, instruction=instruction, constraints=constraints)
        self.value = self._dict[self.DEFAULT_VALUE] = defaultValue if defaultValue is not None else ""

    def validate(self, value):
        try:
            value = value.strip()
            for constraint in self.constraints:
                constraint.validate(value)
            return value
        except VdtValueTooLongError:
            raise AnswerTooLongException
        except VdtValueTooShortError:
            raise AnswerTooShortException

    @property
    def is_entity_field(self):
        return self._dict.get(self.ENTITY_QUESTION_FLAG)

    def get_constraint_text(self):
        if not is_empty(self.constraints):
            length_constraint = self.constraints[0]
            min = length_constraint.min
            max = length_constraint.max
            if min is not None and max is None:
                constraint_text = "Minimum %s characters" % min
                return constraint_text
            if min is None and max is not None:
                constraint_text = "Upto %s characters" % max
                return constraint_text
            elif min is not None and max is not None:
                constraint_text = "Between %s -- %s characters" % (min, max)
                return constraint_text
        return ""
