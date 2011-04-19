# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from _collections import defaultdict

class Question(object):
    NAME = "name"
    LABEL = "label"
    TYPE = "type"
    SMS_CODE="sms_code"
    DEFAULT_VALUE="defaultValue"

    _DEFAULT_VALUES = {
        NAME: "",
        TYPE: "",
        SMS_CODE:"",
        DEFAULT_VALUE:""
        }

    _DEFAULT_LANGUAGE_SPECIFIC_VALUES = {
        LABEL: [],
        }

    _DEFAULT_LANGUAGE = "eng"

    def __init__(self, **kwargs):
        self._dict = defaultdict(dict)
        for k, default_value in self._DEFAULT_VALUES.items():
            self._dict[k] = kwargs.get(k, default_value)

        for k,default_langauge_specific_value in self._DEFAULT_LANGUAGE_SPECIFIC_VALUES.items():
            a = kwargs.get('language', self._DEFAULT_LANGUAGE)
            language_dict={a:kwargs.get(k)}
            self._dict[k]=[language_dict]


    def to_json(self):
        return self._dict