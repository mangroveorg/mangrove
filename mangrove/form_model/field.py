# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from dateutil.parser import parse
import re
import abc

from datetime import datetime
from babel.dates import format_date
from mangrove.data_cleaner import TelephoneNumber
from mangrove.datastore.datadict import DataDictType
from mangrove.errors.MangroveException import AnswerTooBigException, AnswerTooSmallException, AnswerWrongType, IncorrectDate, AnswerTooLongException, AnswerTooShortException, GeoCodeFormatException, RequiredFieldNotPresentException
from mangrove.form_model.validation import ChoiceConstraint, GeoCodeConstraint, constraints_factory

from mangrove.utils.types import is_sequence, is_empty, sequence_to_str
from mangrove.validate import VdtValueTooBigError, VdtValueTooSmallError, VdtTypeError, VdtValueTooShortError, VdtValueTooLongError


def create_question_from(dictionary, dbm):
    """
     Given a dictionary that defines a question, this would create a field with all the validations that are
     defined on it.
    """
    type = dictionary.get("type")
    name = dictionary.get("name")
    code = dictionary.get("code")
    is_entity_question = dictionary.get("entity_question_flag")
    label = dictionary.get("label")
    instruction = dictionary.get("instruction")
    required = dictionary.get("required")
    is_event_time_field = dictionary.get("event_time_field_flag")
    ddtype = DataDictType.create_from_json(dictionary.get("ddtype"), dbm)
    if type == field_attributes.TEXT_FIELD:
        return _get_text_field(code, ddtype, dictionary, is_entity_question, label, name, instruction, required)
    elif type == field_attributes.INTEGER_FIELD:
        return _get_integer_field(code, ddtype, dictionary, label, name, instruction, required)
    elif type == field_attributes.DATE_FIELD:
        return _get_date_field(code, ddtype, dictionary, label, name, instruction, required, is_event_time_field)
    elif type == field_attributes.LOCATION_FIELD:
        return _get_geo_code_field(code, ddtype, instruction, label, name, required)
    elif type == field_attributes.SELECT_FIELD or type == field_attributes.MULTISELECT_FIELD:
        return _get_select_field(code, ddtype, dictionary, label, name, type, instruction, required)
    elif type == field_attributes.LIST_FIELD:
        return _get_list_field(name, code, label, ddtype, instruction, required)
    elif type == field_attributes.TELEPHONE_NUMBER_FIELD:
        return _get_telephone_number_field(code, ddtype, dictionary, label, name, instruction, required)
    return None


def _get_text_field(code, ddtype, dictionary, is_entity_question, label, name, instruction, required):
    constraints, constraints_json = [], dictionary.get("constraints")
    if constraints_json is not None:
        constraints = constraints_factory(constraints_json)
    field = TextField(name=name, code=code, label=label, entity_question_flag=is_entity_question,
        constraints=constraints, ddtype=ddtype, instruction=instruction, required=required)
    return field


def _get_telephone_number_field(code, ddtype, dictionary, label, name, instruction, required):
    constraints, constraints_json = [], dictionary.get("constraints")
    if constraints_json is not None:
        constraints = constraints_factory(constraints_json)

    field = TelephoneNumberField(name=name, code=code, label=label, constraints=constraints, ddtype=ddtype,
        instruction=instruction, required=required)

    return field


def _get_integer_field(code, ddtype, dictionary, label, name, instruction, required):
    constraints, constraint_list = [], dictionary.get('constraints')
    if constraint_list is not None:
        constraints = constraints_factory(constraint_list)

    integer_field = IntegerField(name=name, code=code, label=label, ddtype=ddtype, instruction=instruction,
        constraints=constraints, required=required)

    return integer_field


def _get_date_field(code, ddtype, dictionary, label, name, instruction, required, is_event_time_field):
    date_format = dictionary.get("date_format")

    date_field = DateField(name=name, code=code, label=label, date_format=date_format, ddtype=ddtype,
        instruction=instruction, required=required, event_time_field_flag=is_event_time_field)

    return date_field


def _get_select_field(code, ddtype, dictionary, label, name, type, instruction, required):
    choices = dictionary.get("choices")
    single_select = True if type == field_attributes.SELECT_FIELD else False

    field = SelectField(name=name, code=code, label=label, options=choices, single_select_flag=single_select,
        ddtype=ddtype, instruction=instruction, required=required)

    return field


def _get_list_field(name, code, label, ddtype, instruction, required):
    field = HierarchyField(name, code, label, ddtype, instruction=instruction, required=required)

    return field


def _get_geo_code_field(code, ddtype, instruction, label, name, required):
    field = GeoCodeField(name=name, code=code, label=label, ddtype=ddtype, instruction=instruction,
        required=required)

    return field

def field_to_json(object):
    #    assert isinstance(object, Field)
    if isinstance(object, datetime):
        return object.isoformat()
    else:
        return object._to_json_view()


class field_attributes(object):
    """Constants for referencing standard attributes in questionnaire."""
    LANGUAGE = "language"
    FIELD_CODE = "code"
    INSTRUCTION = "instruction"
    INTEGER_FIELD = "integer"
    TEXT_FIELD = "text"
    TELEPHONE_NUMBER_FIELD = "telephone_number"
    SELECT_FIELD = 'select1'
    LOCATION_FIELD = "geocode"
    DATE_FIELD = 'date'
    MULTISELECT_FIELD = 'select'
    DEFAULT_LANGUAGE = "en"
    ENTITY_QUESTION_FLAG = 'entity_question_flag'
    NAME = "name"
    LIST_FIELD = "list"


class Field(object):
    def __init__(self, type="", name="", code="", label='', ddtype=None, instruction='',
                  constraints=None,required=True):
        if not constraints: constraints = []
        self._dict = {}
        assert ddtype is not None
        self._dict = {'name': name, 'type': type, 'code': code, 'ddtype': ddtype, 'instruction': instruction,
                      'label': label,'required':required}
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

    def set_name(self, new_name):
        self._dict["name"] = new_name

    def set_instruction(self, new_instruction):
        self._dict["instruction"] = new_instruction

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

    @property
    def is_event_time_field(self):
        return False


    @property
    def ddtype(self):
        return self._dict.get('ddtype')

    def _to_json(self):
        dict = self._dict.copy()
        dict['instruction'] = self._dict['instruction']
        dict['ddtype'] = dict['ddtype'].to_json()
        return dict

    def _to_json_view(self):
        json = self._to_json()

        if 'constraints' in json:
            constraints = json.pop('constraints')
            for constraint in constraints:
                json[constraint[0]] = constraint[1]
        return json

    def set_value(self, value):
        self.value = value

    def get_constraint_text(self):
        return ""

    def is_required(self):
        return self._dict['required']

    def validate(self, value):
        if self.is_required() and is_empty(value):
            raise RequiredFieldNotPresentException(self.code)

    def _to_str(self):
        if self.value is None :
            return unicode("--")
        return unicode(self.value)

    def xform_constraints(self):
        return " and ".join(filter(None, [constraint.xform_constraint() for constraint in self.constraints]))

    @abc.abstractmethod
    def formatted_field_values_for_excel(self, value):
        pass

class IntegerField(Field):
    def __init__(self, name, code, label, ddtype, instruction=None,
                 constraints=None, required=True):
        if not constraints: constraints = []
        Field.__init__(self, type=field_attributes.INTEGER_FIELD, name=name, code=code,
                       label=label,  ddtype=ddtype, instruction=instruction, constraints=constraints, required=required)

    def validate(self, value):
        Field.validate(self,value)
        try:
            for constraint in self.constraints:
                constraint.validate(value)
            try:
                return int(value)
            except Exception:
                return float(value)
        except VdtValueTooBigError:
            raise AnswerTooBigException(self._dict[field_attributes.FIELD_CODE], value)
        except VdtValueTooSmallError:
            raise AnswerTooSmallException(self._dict[field_attributes.FIELD_CODE], value)
        except VdtTypeError:
            raise AnswerWrongType(self._dict[field_attributes.FIELD_CODE], value)

    def get_constraint_text(self):
        max, min = self._get_max_min()
        if min is not None and max is None:
            constraint_text = "Minimum %s" % min
            return constraint_text
        if min is None and max is not None:
            constraint_text = "Upto %s" % max
            return constraint_text
        elif min is not None and max is not None:
            constraint_text = "%s -- %s" % (min, max)
            return constraint_text
        return ""

    def _get_max_min(self):
        max = min = None
        if len(self.constraints) > 0:
            constraint = self.constraints[0]
            min = constraint.min
            max = constraint.max
        return max, min

    def formatted_field_values_for_excel(self,value):
        try:
            return float(value)
        except ValueError:
            return value

class DateField(Field):
    DATE_FORMAT = "date_format"
    DATE_DICTIONARY = {'mm.yyyy': '%m.%Y', 'dd.mm.yyyy': '%d.%m.%Y', 'mm.dd.yyyy': '%m.%d.%Y'}
    FORMAT_DATE_DICTIONARY = {'mm.yyyy': 'MM.yyyy', 'dd.mm.yyyy': 'dd.MM.yyyy', 'mm.dd.yyyy': 'MM.dd.yyyy'}

    def __init__(self, name, code, label, date_format, ddtype, instruction=None,
                  required=True, event_time_field_flag=False):
        Field.__init__(self, type=field_attributes.DATE_FIELD, name=name, code=code,
                       label=label,  ddtype=ddtype, instruction=instruction, required=required)

        self._dict[self.DATE_FORMAT] = date_format
        if event_time_field_flag:
            self._dict['event_time_field_flag'] = event_time_field_flag

    @classmethod
    def get_datetime_format(cls, date_format):
        return cls.DATE_DICTIONARY.get(date_format)

    def validate(self, value):
        Field.validate(self,value)
        try:
            return datetime.strptime(value.strip(), DateField.get_datetime_format(self.date_format))
        except ValueError:
            raise IncorrectDate(self._dict.get(field_attributes.FIELD_CODE), value, self._dict.get(self.DATE_FORMAT))

    @property
    def date_format(self):
        return self._dict.get(self.DATE_FORMAT)

    def get_constraint_text(self):
        return self.date_format

    @property
    def is_event_time_field(self):
        return self._dict.get('event_time_field_flag',False)

    def _to_str(self):
        if self.value is None :
            return unicode("--")
        date_format = self.FORMAT_DATE_DICTIONARY.get(self.date_format)
        return format_date(self.value, date_format) if isinstance(self.value, datetime) else unicode(self.value)

    def formatted_field_values_for_excel(self, value):
        try:
            return datetime.strptime(value, self.DATE_DICTIONARY.get(self.date_format))
        except ValueError:
            return value

class TextField(Field):
    DEFAULT_VALUE = "defaultValue"
    CONSTRAINTS = "constraints"
    ENTITY_QUESTION_FLAG = 'entity_question_flag'

    def __init__(self, name, code, label, ddtype, constraints=None, defaultValue="", instruction=None,
                  entity_question_flag=False,required=True):
        if not constraints: constraints = []
        assert isinstance(constraints, list)
        Field.__init__(self, type=field_attributes.TEXT_FIELD, name=name, code=code,
                       label=label,  ddtype=ddtype, instruction=instruction, constraints=constraints,required=required)
        self.value = self._dict[self.DEFAULT_VALUE] = defaultValue if defaultValue is not None else ""
        if entity_question_flag:
            self._dict[self.ENTITY_QUESTION_FLAG] = entity_question_flag

    def validate(self, value):
        Field.validate(self,value)
        try:
            value = value.strip()
            for constraint in self.constraints:
                constraint.validate(value)
            return value
        except VdtValueTooLongError:
            raise AnswerTooLongException(self._dict[field_attributes.FIELD_CODE], value)
        except VdtValueTooShortError:
            raise AnswerTooShortException(self._dict[field_attributes.FIELD_CODE], value)

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

    def formatted_field_values_for_excel(self, value):
        return value

class TelephoneNumberField(TextField):
    def __init__(self, name, code, label, ddtype, constraints=None, defaultValue=None, instruction=None,
                  required=True):
        if not constraints: constraints = []
        assert isinstance(constraints, list)
        TextField.__init__(self, name=name, code=code, label=label,  ddtype=ddtype,
                           instruction=instruction, constraints=constraints, defaultValue=defaultValue, required=required)
        self._dict['type'] = field_attributes.TELEPHONE_NUMBER_FIELD

    def _clean(self, value):
        return TelephoneNumber().clean(value)

    def validate(self, value):
        value = self._clean(value)
        return super(TelephoneNumberField, self).validate(value)


class HierarchyField(Field):

    def __init__(self, name, code, label, ddtype, instruction=None,
                 required=True):
        Field.__init__(self, type=field_attributes.LIST_FIELD, name=name, code=code,
                       label=label,  ddtype=ddtype, instruction=instruction,required=required)

    def validate(self, value):
        Field.validate(self,value)
        if is_sequence(value) or value is None:
            return value
        return [value]

    def _to_str(self):
        if self.value is None :
            return unicode("--")
        return sequence_to_str(self.value) if isinstance(self.value, list) else unicode(self.value)


class SelectField(Field):
    OPTIONS = "choices"

    def __init__(self, name, code, label, options, ddtype, instruction=None,

                 single_select_flag=True,required=True):
        assert len(options) > 0
        type = field_attributes.SELECT_FIELD if single_select_flag else field_attributes.MULTISELECT_FIELD
        self.single_select_flag = single_select_flag
        Field.__init__(self, type=type, name=name, code=code,
                       label=label,  ddtype=ddtype, instruction=instruction,required=required)
        self._dict[self.OPTIONS] = []
        valid_choices = self._dict[self.OPTIONS]
        if options is not None:
            for option in options:
                if isinstance(option, tuple):
                    single_language_specific_option = {'text': option[0], 'val': option[1]}
                elif isinstance(option, dict):
                    single_language_specific_option = option
                else:
                    single_language_specific_option = {'text': option}
                valid_choices.append(single_language_specific_option)
        self.constraint = ChoiceConstraint(
            list_of_valid_choices=[each.get('text') for each in valid_choices],
            single_select_constraint=single_select_flag, code=code)

    SINGLE_SELECT_FLAG = 'single_select_flag'

    def validate(self, value):
        Field.validate(self,value)
        return self.constraint.validate(answer=value.replace(' ','')) #data from ODK collect is submitted with spaces

    @property
    def options(self):
        return self._dict.get(self.OPTIONS)

    def _to_json_view(self):
        dict = self._dict.copy()
        dict['ddtype'] = dict['ddtype'].to_json()
        return dict

    def get_constraint_text(self):
        return [option["text"] for option in self.options]

    def _to_str(self):
        if self.value is None :
            return unicode("--")
        return unicode(",".join(self.value)) if isinstance(self.value, list) else unicode(self.value)

    def _get_value_by_option(self, option):
        for opt in self.options:
            opt_text = opt['text']
            opt_value = opt['val']
            if opt_value.lower() == option.lower():
                return opt_text
        return None

    def formatted_field_values_for_excel(self, value):
        if value is None: return []

        options = re.findall(r'[1-9]?[a-zA-Z]', value)
        result = []
        for option in options:
            option_value = self._get_value_by_option(option)
            if option_value:
                result.append(option_value)
        return result

class GeoCodeField(Field):

    type = field_attributes.LOCATION_FIELD

    def __init__(self, name, code, label, ddtype, instruction=None, required=True):
        Field.__init__(self, type=field_attributes.LOCATION_FIELD, name=name, code=code,
                       label=label,  ddtype=ddtype, instruction=instruction,required=required)

    def validate(self, lat_long_string):
        Field.validate(self,lat_long_string)
        lat_long = lat_long_string.replace(",", " ").strip().split()
        if len(lat_long) < 2:
            raise GeoCodeFormatException(self.code)
        return GeoCodeConstraint().validate(latitude=lat_long[0], longitude=lat_long[1])

    def get_constraint_text(self):
        return "xx.xxxx yy.yyyy"

    def _to_str(self):
        if self.value is None :
            return unicode("--")
        return ", ".join(str(b) for b in list(self.value)) if isinstance(self.value, list) or isinstance(self.value, tuple) else unicode(self.value)

    def formatted_field_values_for_excel(self, value):
        value_list = value.replace(',', ' ').split(' ')
        return self._empty_if_no_data(value_list,0),self._empty_if_no_data(value_list,1)

    def _empty_if_no_data(self,list, index):
        if len(list) < index + 1 :
            return ''
        else:
            try:
                return float(list[index])
            except ValueError:
                return list[index]
