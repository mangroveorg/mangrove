# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from calendar import timegm

from datetime import datetime
import iso8601
import pytz
import time
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
    """""Returns a tz aware datetime in UTC for given datetime.

    NOTE: if passed in datetime is naive, it assumes it is in UTC
    """""
    assert isinstance(d, datetime)
    if is_naive_datetime(d):
        # assume was in UTC!
        d = d.replace(tzinfo=pytz.UTC)
    else:
        d = d.astimezone(pytz.UTC)
    return d


def to_naive_utc(d):
    """Returns a naive (no timezone) datetime in UTC."""
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


def convert_date_string_in_UTC_to_epoch(value):
    """
    Convert the time in '%d-%m-%Y %H:%M:%S' format as per UTC time zone to seconds since the Epoch.
    """
    if is_empty(value):
        return None
    date_time = datetime.strptime(value, '%d-%m-%Y %H:%M:%S').replace(tzinfo=pytz.UTC)
    return convert_date_time_to_epoch(date_time)

def convert_date_time_to_epoch(date_time, tzinfo=None):
    if not isinstance(date_time, datetime):
        date_time = datetime(year=date_time.year, month=date_time.month, day=date_time.day,tzinfo=tzinfo)
    if is_naive_datetime(date_time):
        return int(time.mktime(date_time.timetuple())) * 1000 + date_time.microsecond / 1000
    else:
        return int(timegm(date_time.astimezone(pytz.UTC).timetuple())) * 1000 + date_time.microsecond / 1000
