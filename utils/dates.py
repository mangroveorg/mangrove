# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
import iso8601
import pytz
from types import is_empty, is_string


def parse_iso_date_str(s):
    # wrap call to iso8601 parser to return ValueError on
    # all failures
    try:
        return to_aware_utc(iso8601.parse_date(s))
    except Exception:
        raise ValueError("datestring not valid format")


def is_naive_datetime(d):
    assert isinstance(d, datetime)
    return d.tzinfo is None


def to_aware_utc(d):
    '''Returns a tz aware datetime in UTC for given datetime.

    NOTE: if passed in datetime is naive, it assumes it is in UTC
    '''
    assert isinstance(d, datetime)
    if is_naive_datetime(d):
        # assume was in UTC!
        d = d.replace(tzinfo=pytz.UTC)
    else:
        d = d.astimezone(pytz.UTC)
    return d


def to_naive_utc(d):
    '''Returns a naive (no timezone) datetime in UTC.

    NOTE: if inbound datetime is naive, it assumes it's already UTC and returns as is
    '''
    assert isinstance(d, datetime)
    if not is_naive_datetime(d):
        d = d.astimezone(pytz.UTC).replace(tzinfo=None)
    return d


def utcnow():
    return to_aware_utc(datetime.utcnow())


def py_datetime_to_js_datestring(d):
    if not isinstance(d, datetime):
        raise ValueError("not a datetime")
    return to_aware_utc(d).isoformat()


def js_datestring_to_py_datetime(s):
    if not is_string(s):
        raise ValueError("Not a valid string")
    if is_empty(s):
        raise ValueError("Not a valid datetime string")
    return to_aware_utc(parse_iso_date_str(s))
