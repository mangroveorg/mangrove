# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from _collections import defaultdict
from copy import deepcopy

class question_attributes(object):
    '''Constants for referencing standard attributes in questionnaire.'''
    LANGUAGE="language"

class Question(object):
    NAME = "name"
    LABEL = "label"
    TYPE = "type"
    SMS_CODE = "sms_code"

    _DEFAULT_VALUES = {
        NAME: "",
        TYPE: "",
        SMS_CODE: "",
        }

    _DEFAULT_LANGUAGE_SPECIFIC_VALUES = {
        LABEL: [],
        }

    _DEFAULT_LANGUAGE = "eng"

    def __init__(self, **kwargs):
        self._dict = defaultdict(dict)
        for k, default_value in self._DEFAULT_VALUES.items():
            self._dict[k] = kwargs.get(k, default_value)

        for k, default_langauge_specific_value in self._DEFAULT_LANGUAGE_SPECIFIC_VALUES.items():
            a = kwargs.get(question_attributes.LANGUAGE, self._DEFAULT_LANGUAGE)
            language_dict = {a: kwargs.get(k)}
            self._dict[k] = [language_dict]


    def to_json(self):
        return self._dict


class IntegerQuestion(Question):
    RANGE = "range"
    _INTEGER_QUESTION_DEFAULT_VALUES = {
        RANGE: {}
        }


    def __init__(self, **kwargs):
        Question.__init__(self, **kwargs)
        for k, default_value in self._INTEGER_QUESTION_DEFAULT_VALUES.items():
            self._dict[k] = kwargs.get(k, default_value)


class TextQuestion(Question):
    DEFAULT_VALUE = "defaultValue"
    _TEXT_QUESTION_DEFAULT_VALUES = {
        DEFAULT_VALUE: ""
        }


    def __init__(self, **kwargs):
        Question.__init__(self, **kwargs)
        for k, default_value in self._TEXT_QUESTION_DEFAULT_VALUES.items():
            self._dict[k] = kwargs.get(k, default_value)


class SelectQuestion(Question):
    OPTIONS = "options"
    _SELECT1_QUESTION_DEFAULT_VALUES = {
        OPTIONS: []
    }

    def __init__(self, **kwargs):
        print "the default value before is is"
        print self._SELECT1_QUESTION_DEFAULT_VALUES.items()
        Question.__init__(self, **kwargs)
        print "the default value is"
        print self._SELECT1_QUESTION_DEFAULT_VALUES.items()
        for k, default_value in self._SELECT1_QUESTION_DEFAULT_VALUES.items():
            print "the default value before saving dict is"
            self._dict[k] = deepcopy(default_value)
            print "the default value after saving dict is"
            for option in kwargs.get(k):
                language = kwargs.get(question_attributes.LANGUAGE,self._DEFAULT_LANGUAGE)
                if isinstance(option, tuple):
                    #"options": [{"text": {"eng": "RED"},"val": 1},{"text": {"eng": "YELLOW"},"val": 2}]
                    single_language_specific_option = {'text': [{language: option[0]}], 'val': option[1]}
                else:
                    single_language_specific_option = {'text': [{language: option}]}

                self._dict[k].append(single_language_specific_option)

        print "the default value at the end of init is"
        print self._SELECT1_QUESTION_DEFAULT_VALUES.items()




class QuestionBuilder(object):
    TYPES = ('integer', 'text', 'select1')

    TYPES_CLASSES = (IntegerQuestion, TextQuestion, SelectQuestion)

    TYPES_NAMES_TO_CLASSES = zip(TYPES, TYPES_CLASSES)

    def __new__(cls, *args, **kwargs):
        """
        Create the proper QuestionType according to the name passed
        """

        try:
            type_name = cls._clean(kwargs.get("type"))
        except IndexError:
            raise Exception('You must pass type as '\
                                'keyword argument')
        
        mapping = dict(cls.TYPES_NAMES_TO_CLASSES)
        return mapping[type_name](**kwargs)


    @classmethod
    def _clean(cls, type_name):
        """
        Normalize the type name, then check if it is a valid type name.
        """
        type_name = type_name.lower()
        if type_name not in cls.TYPES:
            raise Exception('"%(type_name)s" is not a valid type name. '\
                                'Choose among: "%(allowed_type_names)s"' % {
                    'type_name': type_name,
                    'allowed_type_names': '", "'.join(cls.TYPES) })
        return type_name

