# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.errors.MangroveException import AnswerNotInListException, AnswerHasTooManyValuesException, AnswerHasNoValuesException, LatitudeNotFloat, LongitudeNotFloat, LatitudeNotInRange, LongitudeNotInRange

from validate import is_string, is_float, VdtTypeError, VdtValueError


class ConstraintAttributes(object):
    MAX = "max"
    MIN = "min"
    MIN_LONG = -180
    MAX_LONG = 180
    MIN_LAT = -90
    MAX_LAT = 90


class NumericConstraint(object):
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
        return is_float(value, min=self.min, max=self.max)


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
    def __init__(self, single_select_constraint, list_of_valid_choices, code):
        self.single_select_constraint = single_select_constraint
        self.list_of_valid_choices = list_of_valid_choices
        self.code = code

    def validate(self, answer):
        assert answer is not None
        answer_string = answer.lower().strip()
        if not answer_string:
            raise AnswerHasNoValuesException(code=self.code, answer=answer)
        choices = []
        if self.single_select_constraint and  len(answer_string) > 1:
            raise AnswerHasTooManyValuesException(code=self.code, answer=answer)
        for character in answer_string:
            index_represented = ord(character) - ord('a')
            if index_represented > len(self.list_of_valid_choices) - 1 or index_represented < 0:
                raise AnswerNotInListException(code=self.code, answer=character)
            else:
                choice_selected = self.list_of_valid_choices[index_represented]
                if choice_selected not in choices:
                    choices.append(choice_selected)
        return choices


class LocationConstraint(object):
    def validate(self, latitude, longitude):
        try:
            lat = is_float(latitude, min=ConstraintAttributes.MIN_LAT, max=ConstraintAttributes.MAX_LAT)
        except VdtTypeError:
            raise LatitudeNotFloat(latitude)
        except VdtValueError:
            raise LatitudeNotInRange(latitude)
        try:
            long = is_float(longitude, min=ConstraintAttributes.MIN_LONG, max=ConstraintAttributes.MAX_LONG)
        except VdtTypeError:
            raise LongitudeNotFloat(longitude)
        except VdtValueError:
            raise LongitudeNotInRange(longitude)
        return lat, long