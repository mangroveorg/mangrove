# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from _collections import defaultdict

class question_attributes(object):
    '''Constants for referencing standard attributes in questionnaire.'''
    LANGUAGE = "language"
    QUESTION_CODE = "question_code"
    INTEGER_QUESTION = "integer"
    TEXT_QUESTION = "text"
    SELECT_QUESTION = 'select1'
    DEFAULT_LANGUAGE = "eng"

class Question(object):
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
            a = kwargs.get(question_attributes.LANGUAGE, question_attributes.DEFAULT_LANGUAGE)
            language_dict = {a: kwargs.get(k)}
            self._dict[k] = language_dict


    def _to_json(self):
        return self._dict

    def add_or_edit_label(self, label, language=None):
        language_to_add = language if language is not None else question_attributes.DEFAULT_LANGUAGE
        self._dict[self.LABEL][language_to_add] = label


class IntegerQuestion(Question):
    RANGE = "range"

    def __init__(self, name, question_code, label, range=None, language=question_attributes.DEFAULT_LANGUAGE):
        Question.__init__(self, type=question_attributes.INTEGER_QUESTION, name=name, question_code=question_code,
                          label=label, language=language)
        self._dict[self.RANGE] = range if range is not None else {}


class TextQuestion(Question):
    DEFAULT_VALUE = "defaultValue"


    def __init__(self, name, question_code, label, defaultValue=None, language=question_attributes.DEFAULT_LANGUAGE):
        Question.__init__(self, type=question_attributes.TEXT_QUESTION, name=name, question_code=question_code,
                          label=label, language=language)
        self._dict[self.DEFAULT_VALUE] = defaultValue if defaultValue is not None else ""


class SelectQuestion(Question):
    OPTIONS = "options"

    def __init__(self, name, question_code, label, options=None, language=question_attributes.DEFAULT_LANGUAGE):
        Question.__init__(self, type=question_attributes.SELECT_QUESTION, name=name, question_code=question_code,
                          label=label, language=language)
        self._dict[self.OPTIONS] = []
        for option in options:
            if isinstance(option, tuple):
                single_language_specific_option = {'text': [{language: option[0]}], 'val': option[1]}
            else:
                single_language_specific_option = {'text': [{language: option}]}

            self._dict[self.OPTIONS].append(single_language_specific_option)
