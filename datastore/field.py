# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from _collections import defaultdict

class field_attributes(object):

    '''Constants for referencing standard attributes in questionnaire.'''
    LANGUAGE = "language"
    FIELD_CODE = "question_code"
    INTEGER_FIELD = "integer"
    TEXT_FIELD = "text"
    SELECT_FIELD = 'select1'
    DATE_FIELD = 'date'
    MULTISELECT_FIELD = 'select'
    DEFAULT_LANGUAGE = "eng"
    ENTITY_QUESTION_FLAG = 'entity_question_flag'
    NAME = "name"

class Field(object):
    NAME = "name"
    LABEL = "label"
    TYPE = "type"
    QUESTION_CODE = "question_code"

    _DEFAULT_VALUES = {
        NAME: "",
        TYPE: "",
        QUESTION_CODE: "",
    }

    _DEFAULT_LANGUAGE_SPECIFIC_VALUES = {
        LABEL: {},
    }

    def __init__(self, **kwargs):
        self._dict = defaultdict(dict)
        for k, default_value in self._DEFAULT_VALUES.items():
            self._dict[k] = kwargs.get(k, default_value)

        for k, default_langauge_specific_value in self._DEFAULT_LANGUAGE_SPECIFIC_VALUES.items():
            a = kwargs.get(field_attributes.LANGUAGE, field_attributes.DEFAULT_LANGUAGE)
            language_dict = {a: kwargs.get(k)}
            self._dict[k] = language_dict


    def _to_json(self):
        return self._dict

    def add_or_edit_label(self, label, language=None):
        language_to_add = language if language is not None else field_attributes.DEFAULT_LANGUAGE
        self._dict[self.LABEL][language_to_add] = label


class IntegerField(Field):
    RANGE = "range"

    def __init__(self, name, question_code, label, range=None, language=field_attributes.DEFAULT_LANGUAGE):
        Field.__init__(self, type=field_attributes.INTEGER_FIELD, name=name, question_code=question_code,
                          label=label, language=language)
        self._dict[self.RANGE] = range if range is not None else {}


class TextField(Field):
    DEFAULT_VALUE = "defaultValue"
    ENTITY_QUESTION_FLAG = 'entity_question_flag'

    def __init__(self, name, question_code, label, defaultValue=None, language=field_attributes.DEFAULT_LANGUAGE,entity_question_flag=False):
        Field.__init__(self, type=field_attributes.TEXT_FIELD, name=name, question_code=question_code,
                          label=label, language=language)
        self._dict[self.DEFAULT_VALUE] = defaultValue if defaultValue is not None else ""
        if entity_question_flag:
            self._dict[self.ENTITY_QUESTION_FLAG] = entity_question_flag

class SelectField(Field):
    OPTIONS = "options"
    SINGLE_SELECT_FLAG = 'single_select_flag'

    def __init__(self, name, question_code, label, options=None, language=field_attributes.DEFAULT_LANGUAGE,single_select_flag=True):
        type = field_attributes.SELECT_FIELD if single_select_flag else field_attributes.MULTISELECT_FIELD
        self.SINGLE_SELECT_FLAG = single_select_flag
        Field.__init__(self, type=type, name=name, question_code=question_code,
                          label=label, language=language)
        self._dict[self.OPTIONS] = []
        for option in options:
            if isinstance(option, tuple):
                single_language_specific_option = {'text': [{language: option[0]}], 'val': option[1]}
            else:
                single_language_specific_option = {'text': [{language: option}]}

            self._dict[self.OPTIONS].append(single_language_specific_option)



class DateField(Field):
    RANGE = "range"
    FORMAT="format"
    def __init__(self,name, question_code, label,format,range=None,language=field_attributes.DEFAULT_LANGUAGE):
        Field.__init__(self, type=field_attributes.DATE_FIELD, name=name, question_code=question_code,
                          label=label, language=language)

        self._dict[self.RANGE] = range if range is not None else {}
        self._dict[self.FORMAT] = format if format is not None else ""
