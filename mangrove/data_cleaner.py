# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.validate import is_float

class TelephoneNumber(object):
    def _strip_decimals(self, number_as_given):
        return unicode(long(number_as_given))

    def _clean_epsilon_format(self, value):
        if value.startswith('0'):
            return value
        try:
            value = self._strip_decimals(is_float(value))
        except Exception:
            pass
        return value

    def _clean_digits(self, value):
        if value is not None:
            return "".join([num for num in value if num != '-'])
        return value

    def clean(self, value):
        value = self._clean_epsilon_format(value)
        return self._clean_digits(value)
