# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.errors.MangroveException import EntityQuestionCodeNotSubmitted
from mangrove.form_model.field import TextField
from collections import OrderedDict

def case_insensitive_lookup(values, code):
    for fieldcode in values:
        if fieldcode.lower() == code.lower():
            return values[fieldcode]
    return None

class MandatoryValidator(object):

    def get_mandatory_fields(self, fields):
        return [field for field in fields if field.is_required()]


    def validate(self,values,fields):
        mandatory_fields = self.get_mandatory_fields(fields)
        return OrderedDict({field.code:"Mandatory Field with code: %s is not present" % (field.code,) for field in mandatory_fields if case_insensitive_lookup(values, field.code) is None})


class EntityQuestionAnsweredValidator(object):

    def validate(self,values,fields):
        entity_question = [field for field in fields if isinstance(field,TextField) and field.is_entity_field][0]
        if case_insensitive_lookup(values, entity_question.code) is None:
            raise EntityQuestionCodeNotSubmitted()
        return OrderedDict({})