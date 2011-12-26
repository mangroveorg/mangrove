# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import re
from mangrove.errors.MangroveException import MangroveException

from mangrove.errors.MangroveException import AnswerNotInListException, AnswerHasTooManyValuesException, AnswerHasNoValuesException, LatitudeNotFloat, LongitudeNotFloat, LatitudeNotInRange, LongitudeNotInRange, RegexMismatchException
from mangrove.validate import is_string, is_float, VdtTypeError, VdtValueError

EMPTY_VALUES = (None, '', [], (), {})

class NumericRangeValidator(object):
    MAX = "max"
    MIN = "min"
    def __init__(self, min=None, max=None):
        self.min = min
        self.max = max

    def _to_json(self):
        dict = {'_class': 'NumericRangeValidator'}
        if self.min is not None:
            dict[self.MIN] = self.min
        if self.max is not None:
            dict[self.MAX] = self.max
        return dict

    def validate(self, value):
        if is_float(value, min=self.min, max=self.max):
            return is_float(value, min=self.min, max=self.max)
        else:
            raise MangroveException


class TextLengthValidator(NumericRangeValidator):
    def _to_json(self):
        dict = {'_class': 'TextLengthValidator'}
        if self.min is not None:
            dict[self.MIN] = self.min
        if self.max is not None:
            dict[self.MAX] = self.max
        return dict

    def validate(self, value):
        if is_string(value.strip(), min=self.min, max=self.max):
            return is_string(value.strip(), min=self.min, max=self.max)
        else:
            raise MangroveException


class ChoiceValidator(object):

    def __init__(self, single_select_constraint, list_of_valid_choices):
        self.single_select_constraint = single_select_constraint
        self.list_of_valid_choices = list_of_valid_choices

    def _to_json(self):
        return self.__dict__ + {'_class': 'ChoiceValidator'}

    def validate(self, answer, code):
        assert answer is not None
        answer_string = answer.lower().strip()
        if not answer_string:
            raise AnswerHasNoValuesException(code=code, answer=answer)
        choices = []
        if self.single_select_constraint and  len(answer_string) > 1:
            raise AnswerHasTooManyValuesException(code=code, answer=answer)
        for character in answer_string:
            index_represented = ord(character) - ord('a')
            if index_represented > len(self.list_of_valid_choices) - 1 or index_represented < 0:
                raise AnswerNotInListException(code=code, answer=character)
            else:
                choice_selected = self.list_of_valid_choices[index_represented]
                if choice_selected not in choices:
                    choices.append(choice_selected)
        return choices


class GeoCodeValidator(object):
    MIN_LONG = -180
    MAX_LONG = 180
    MIN_LAT = -90
    MAX_LAT = 90

    def _to_json(self):
        return {'_class':'GeoCodeValidator'}
    
    def validate(self, latitude, longitude):
        latitude=latitude.encode('ascii','ignore')
        longitude=longitude.encode('ascii','ignore')
        try:
            lat = is_float(latitude, min=self.MIN_LAT, max=self.MAX_LAT)
        except VdtTypeError:
            raise LatitudeNotFloat(latitude)
        except VdtValueError:
            raise LatitudeNotInRange(latitude)
        try:
            long = is_float(longitude, min=self.MIN_LONG, max=self.MAX_LONG)
        except VdtTypeError:
            raise LongitudeNotFloat(longitude)
        except VdtValueError:
            raise LongitudeNotInRange(longitude)
        return lat, long

class RegexValidator(object):
    def __init__(self, pattern=None):
        self.pattern = pattern

    def validate(self, text):
        if re.match(self.pattern, text):
            return text
        raise RegexMismatchException(self.pattern)

    def _to_json(self):
        return {
            '_class':'RegexValidator',
            'pattern': self.pattern
        }

def validator_factory(constraints_json):
    constraints = []
    for constraint_json in constraints_json:
        constraint_class = constraint_json.pop('_class')
        constraints.append(type(constraint_class, (eval(constraint_class),), {})(**constraint_json))
    return constraints
