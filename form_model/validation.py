# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

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
        return is_string(value, min=self.min, max=self.max)
