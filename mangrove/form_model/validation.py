
import re
from mangrove.errors.MangroveException import AnswerNotInListException, AnswerHasTooManyValuesException, AnswerHasNoValuesException, LatitudeNotFloat, LongitudeNotFloat, LatitudeNotInRange, LongitudeNotInRange, RegexMismatchException, ShortCodeRegexMismatchException
from mangrove.utils.types import is_empty
from mangrove.utils.helpers import find_index_represented

from mangrove.validate import is_string, is_float, VdtTypeError, VdtValueError


class ConstraintTypes(object):
    REGEX = 'regex'
    SELECT = 'select'
    RANGE = 'range'
    LENGTH = 'length'
    GEO = 'geo'
    SHORT_CODE = 'short_code'


class ConstraintAttributes(object):
    MAX = "max"
    MIN = "min"
    MIN_LONG = -180
    MAX_LONG = 180
    MIN_LAT = -90
    MAX_LAT = 90
    PATTERN = '_pattern'


class NumericRangeConstraint(object):
    def __init__(self, min=None, max=None, dict=None):
        self.min = min
        self.max = max
        if dict is not None:
            self.min = dict.get('min')
            self.max = dict.get('max')

    def _to_json(self):
        dict = {}
        if self.min is not None:
            dict[ConstraintAttributes.MIN] = self.min
        if self.max is not None:
            dict[ConstraintAttributes.MAX] = self.max
        return ('range', dict)

    def validate(self, value):
        return is_float(value, min=self.min, max=self.max)

    def xform_constraint(self):
        min_constraint = ". &gt;= {0}".format(self.min) if self.min else None
        max_constraint = ". &lt;= {0}".format(self.max) if self.max else None
        return " and ".join(filter(None, [min_constraint, max_constraint]))


class TextLengthConstraint(NumericRangeConstraint):
    def _to_json(self):
        dict = {}
        if self.min is not None:
            dict[ConstraintAttributes.MIN] = self.min
        if self.max is not None:
            dict[ConstraintAttributes.MAX] = self.max
        return ("length", dict) if not is_empty(dict) else ()

    def validate(self, value):
        return is_string(value.strip(), min=self.min, max=self.max)

    def xform_constraint(self):
        min_constraint = "string-length(.) &gt;= {0}".format(self.min) if self.min else None
        max_constraint = "string-length(.) &lt;= {0}".format(self.max) if self.max else None
        return " and ".join(filter(None, [min_constraint, max_constraint]))


class ChoiceConstraint(object):
    def __init__(self, single_select_constraint, list_of_valid_choices, code, dict=None):
        self.single_select_constraint = single_select_constraint
        self.list_of_valid_choices = list_of_valid_choices
        self.code = code

    def validate(self, answer):
        assert answer is not None
        answer_string = answer.lower().strip()
        if not answer_string:
            raise AnswerHasNoValuesException(code=self.code, answer=answer)
        choices = []
        responses = re.findall(r'[1-9]?[a-z]', answer_string)

        if self.single_select_constraint and len(responses) > 1:
            raise AnswerHasTooManyValuesException(code=self.code, answer=answer)

        invalid_responses = re.split(r'[1-9]?[a-z]', answer_string)
        invalid_responses = filter(None, invalid_responses)

        if len(invalid_responses) > 0:
            raise AnswerNotInListException(code=self.code, answer=invalid_responses[0])

        for response in responses:
            index_represented = find_index_represented(response)
            if index_represented > len(self.list_of_valid_choices) - 1 or index_represented < 0:
                raise AnswerNotInListException(code=self.code, answer=response)
            else:
                choice_selected = self.list_of_valid_choices[index_represented]
                if choice_selected not in choices:
                    choices.append(choice_selected)
        return choices


class GeoCodeConstraint(object):
    def validate(self, latitude, longitude):
        latitude = latitude.strip(u'\u200e')
        longitude = longitude.strip(u'\u200e')
        latitude = latitude.encode('ascii')
        longitude = longitude.encode('ascii')
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


class RegexConstraint(object):
    def __init__(self, reg=None, dict=None):
        self._pattern = dict if dict is not None else reg

    def validate(self, text):
        if re.match(self._pattern, text):
            return text
        raise RegexMismatchException(self._pattern)

    @property
    def pattern(self):
        return self._pattern

    def _to_json(self):
        return ('regex', self._pattern)


class ShortCodeRegexConstraint(object):
    def __init__(self, reg=None, dict=None):
        self._pattern = dict if dict is not None else reg

    def validate(self, text):
        if re.match(self._pattern, text):
            return text.lower()
        raise ShortCodeRegexMismatchException(self._pattern)

    @property
    def pattern(self):
        return self._pattern

    def _to_json(self):
        return ('short_code', self._pattern)


def constraints_factory(constraints_json):
    constraints = []
    for constraint_type, constraint_json in constraints_json:
        constraint_class = constraint_for.get(constraint_type)
        if constraint_class is not None:
            constraints.append(constraint_class(dict=constraint_json))
    return constraints


constraint_for = {
    ConstraintTypes.LENGTH: TextLengthConstraint,
    ConstraintTypes.RANGE: NumericRangeConstraint,
    ConstraintTypes.SELECT: ChoiceConstraint,
    ConstraintTypes.GEO: GeoCodeConstraint,
    ConstraintTypes.REGEX: RegexConstraint,
    ConstraintTypes.SHORT_CODE: ShortCodeRegexConstraint,


}