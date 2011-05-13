# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from xml.etree.ElementTree import parse
from mangrove.errors.MangroveException import AnswerNotInListException, AnswerHasTooManyValuesException, AnswerHasNoValuesException

from validate import is_integer, is_string


class ConstraintAttributes(object):
    MAX = "max"
    MIN = "min"


class IntegerConstraint(object):
    def __init__(self, min=None, max=None):
        self.min = min
        self.max = max

    def _to_json(self):
        dict = {}
        if self.min is not None:
            dict[ConstraintAttributes.MIN] = self.min
        if self.max is not None:
            dict[ConstraintAttributes.MAX] = self.max
        return dict

    def validate(self, value):
        return is_integer(value, min=self.min, max=self.max)


class TextConstraint(object):
    def __init__(self, min=None, max=None):
        self.min = min
        self.max = max

    def _to_json(self):
        dict = {}
        if self.min is not None:
            dict[ConstraintAttributes.MIN] = self.min
        if self.max is not None:
            dict[ConstraintAttributes.MAX] = self.max
        return dict

    def validate(self, value):
        return is_string(value.strip(), min=self.min, max=self.max)


class ChoiceConstraint(object):
    def __init__(self, single_select_constraint, list_of_valid_choices, question_code):
        self.single_select_constraint = single_select_constraint
        self.list_of_valid_choices = list_of_valid_choices
        self.question_code = question_code

    def validate(self, answer):
        assert answer is not None
        answer_string = answer.lower().strip()
        if not answer_string:
            raise AnswerHasNoValuesException(question_code=self.question_code, answer=answer)
        choices = []
        if self.single_select_constraint and  len(answer_string) > 1:
            raise AnswerHasTooManyValuesException(question_code=self.question_code, answer=answer)
        for character in answer_string:
            try:
                index_represented = int(character) - 1
            except ValueError:
                index_represented = ord(character) - ord('a')
            if index_represented > len(self.list_of_valid_choices) - 1:
                raise AnswerNotInListException(question_code=self.question_code, answer=character)
            else:
                choice_selected = self.list_of_valid_choices[index_represented]
                if (choice_selected not in choices):
                    choices.append(choice_selected)
        return choices
