# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.utils.dates import convert_date_time_to_epoch

__author__ = 'jwishnie'

from unittest  import TestCase
from datetime import datetime, date
from mangrove import utils
from mangrove.utils import types

import pytz

try:
    import json
except ImportError:
    import simplejson as json

class TestTypeUtils(TestCase):
    an_int = 1
    a_float = 2.1
    a_bool = True
    true_strings = ('y', 'Y', 'yes', 'yeS', 'yES', 'YES', 'Yes', '1', 't', 'T', 'True', 'TrUe',
                    u'y', u'Y', u'yes', u'yeS', u'yES', u'YES', u'Yes', u'1', u't', u'T', u'True', u'TrUe',
        )
    not_true_strings = ('a', u"v", 0, None, ())
    a_datetime = datetime.now()
    a_list = [1, 2]
    a_tuple = (1, 2)
    a_dict = {1: 2}
    a_blank_string = ''
    a_blank_unicode = u''
    a_ws_string = '          '
    a_ws_unicode = u'       '
    a_string = 'abc'
    a_unicode = u'你好吗？'
    a_nonempty_ws_unicode = u'      你好吗？    '
    a_nonempty_ws_string = '      ab c  '
    an_empty_list = []
    an_empty_dict = {}
    an_empty_tuple = ()

    empties = (
        None, a_blank_string, a_ws_string, an_empty_dict,
        an_empty_list, an_empty_tuple, a_blank_unicode, a_ws_unicode
        )

    non_empties = (
        an_int, a_float, a_bool, a_datetime, a_list, a_tuple, a_dict,
        a_string, a_nonempty_ws_string, a_unicode, a_nonempty_ws_unicode
        )

    seqs = (a_list, a_tuple, an_empty_list, an_empty_tuple, true_strings, not_true_strings)

    non_seqs = (
        None, an_int, a_float, a_bool, a_string, a_blank_string, a_nonempty_ws_string,
        a_unicode, a_blank_unicode, a_ws_unicode, a_nonempty_ws_unicode, a_dict, an_empty_dict,
        )

    iters = seqs + (a_dict, an_empty_dict)

    non_iters = non_seqs[:-2]  # remove dicts

    nums = (an_int, a_float)
    non_nums = (None, a_list, a_tuple, a_dict, a_blank_string, a_nonempty_ws_string, a_string, an_empty_dict,
                an_empty_list, an_empty_tuple, a_unicode, a_blank_unicode, a_ws_unicode, a_nonempty_ws_unicode
        )

    strs = (
        a_string, a_unicode, a_ws_string, a_ws_unicode,
        a_nonempty_ws_unicode, a_nonempty_ws_string, a_blank_unicode, a_blank_string
        )

    non_strs = (
        None, an_int, a_float, a_bool, a_datetime, a_list, a_tuple, a_dict, an_empty_dict,
        an_empty_list, an_empty_tuple
        )

    bools = (True, False)
    non_bools = (
        None, a_blank_string, a_ws_string, an_empty_dict,
        an_empty_list, an_empty_tuple, a_blank_unicode, a_ws_unicode,
        an_int, a_float, a_datetime, a_list, a_tuple, a_dict,
        a_string, a_nonempty_ws_string, a_unicode, a_nonempty_ws_unicode
        )

    def _test_a_list(self, pos, neg, test, pos_fail_msg, neg_fail_msg):
        if pos is not None:
            for pos in pos:
                self.assertTrue(test(pos), "'%s' %s" % (unicode(pos), pos_fail_msg))

        if neg is not None:
            for neg in neg:
                self.assertFalse(test(neg), "'%s' %s" % (unicode(neg), neg_fail_msg))

    def test_empty(self):
        self._test_a_list(self.empties, self.non_empties, utils.types.is_empty,
                          "failed 'is_empty'", "passed 'is_empty'")

    def test_not_empty(self):
        self._test_a_list(self.non_empties, self.empties, utils.types.is_not_empty,
                          "failed 'is_not_empty'", "passed 'is_not_empty'")

    def test_is_sequence(self):
        self._test_a_list(self.seqs, self.non_seqs, utils.types.is_sequence,
                          "failed 'is_sequence'", "passed 'is_sequence'")

    def test_is_iterable(self):
        self._test_a_list(self.iters, self.non_iters, utils.types.is_iterable,
                          "failed 'is_iterable'", "passed 'is_iterable'")

    def test_is_number(self):
        self._test_a_list([True, False] + list(self.nums), self.non_nums, utils.types.is_number,
                          "failed 'is_number'", "passed 'is_number'")

    def test_is_string(self):
        self._test_a_list(self.strs, self.non_strs, utils.types.is_string,
                          "failed 'is_string'", "passed 'is_string'")

    def test_string_as_bool(self):
        self._test_a_list(self.true_strings, self.not_true_strings,
                          lambda x: types.string_as_bool(x),
                          ": string_as_bool returned 'False'", ": string_as_bool returned 'True'")

    def test_primitive_type(self):
        self._test_a_list(self.strs, None,
                          lambda x: types.primitive_type(x) == 'text',
                          ": primitive_type returned something other than 'text'", "")

        self._test_a_list(self.nums, None,
                          lambda x: types.primitive_type(x) == 'numeric',
                          ": primitive_type returned something other than 'numeric'", "")

        self._test_a_list([self.a_datetime], None,
                                           lambda x: types.primitive_type(x) == 'datetime',
                                           ": primitive_type returned something other than 'datetime'", "")

        self._test_a_list(self.bools, None,
                          lambda x: types.primitive_type(x) == 'boolean',
                          ": primitive_type returned something other than 'boolean'", "")

        self._test_a_list([None], None,
                                lambda x: types.primitive_type(x) == 'unknown',
                                ": primitive_type returned something other than 'unknown'", "")


class TestDateUtils(TestCase):
    def setUp(self):
        datetuple = (2011, 03, 22, 02, 23, 42)
        self.naive_utc = datetime(*datetuple)
        self.tz_aware_utc = datetime(*datetuple, tzinfo=pytz.UTC)
        self.us_pacific = self.tz_aware_utc.astimezone(pytz.timezone('US/Pacific'))
        self.ist = self.tz_aware_utc.astimezone(pytz.timezone('Asia/Kolkata'))

    def test_should_raise_ValueError_if_invalid_date_string(self):
        self.assertRaises(ValueError, utils.dates.js_datestring_to_py_datetime, "invalid date")
        self.assertRaises(ValueError, utils.dates.js_datestring_to_py_datetime, "")
        self.assertRaises(ValueError, utils.dates.js_datestring_to_py_datetime, " ")
        self.assertRaises(ValueError, utils.dates.js_datestring_to_py_datetime, None)
        self.assertRaises(ValueError, utils.dates.js_datestring_to_py_datetime, 123456)
        self.assertRaises(ValueError, utils.dates.js_datestring_to_py_datetime, '123456')
        self.assertRaises(ValueError, utils.dates.js_datestring_to_py_datetime, datetime.now())

    def test_to_naive_utc(self):
        # make sure tz aware dates convert properly
        self.assertIsNone(utils.dates.to_naive_utc(self.ist).tzinfo)
        self.assertEquals(utils.dates.to_naive_utc(self.ist), self.naive_utc)
        self.assertEquals(utils.dates.to_naive_utc(self.tz_aware_utc), self.naive_utc)
        self.assertEquals(utils.dates.to_naive_utc(self.ist), utils.dates.to_naive_utc(self.us_pacific))

        # make sure naives aren't messed with
        self.assertEqual(utils.dates.to_naive_utc(self.naive_utc), self.naive_utc)

    def test_to_aware_utc(self):
        # make sure a naive converts properly
        aware = utils.dates.to_aware_utc(self.naive_utc)
        self.assertIsNotNone(aware.tzinfo)
        self.assertEqual(pytz.UTC.utcoffset(self.tz_aware_utc),
                         aware.tzinfo.utcoffset(aware))
        self.assertEqual(self.tz_aware_utc, aware)

        # make sure an aware converts properly
        aware = utils.dates.to_aware_utc(self.us_pacific)
        self.assertEqual(aware, self.tz_aware_utc)

        # make sure the actual hour value changed by either 7
        # or 8 hours (depends on daylight savings!)
        self.assertTrue((self.us_pacific.hour + 7) % 24 == aware.hour or
                        (self.us_pacific.hour + 8) % 24 == aware.hour)

    def test_utcnow(self):
        un, dn = utils.dates.utcnow(), datetime.utcnow()

        # make sure utils.utcnow constructed object has a UTC tzinfo
        self.assertEqual(un.tzinfo.utcoffset(un), self.tz_aware_utc.tzinfo.utcoffset(self.tz_aware_utc))

        # hard to test that are equal one as can't make parallel calls to utils and datetime.utcnow!
        # so take them, throw away the microseconds on the assumption that they will be constructed
        # in the same second
        un = un.replace(microsecond=0)
        dn = dn.replace(tzinfo=pytz.UTC, microsecond=0)
        self.assertEqual(un, dn)

    def test_convert_date_time_to_epoch_when_given_a_datetime_object(self):
        date_time = datetime(year=1970, month=1, day=1, tzinfo=pytz.UTC)
        actual_epoch_time = convert_date_time_to_epoch(date_time)
        expected_epoch_time = 0.0
        self.assertEqual(actual_epoch_time,expected_epoch_time)

    def test_convert_date_time_to_epoch_when_given_a_date_object(self):
        date_object_time = date(year=1970, month=1, day=1)
        actual_epoch_time = convert_date_time_to_epoch(date_object_time, pytz.UTC)
        expected_epoch_time = 0.0
        self.assertEqual(actual_epoch_time,expected_epoch_time)


class TestJSONUtils(TestCase):
    def setUp(self):
        self.dt = utils.dates.utcnow()
        self.dict_with_dt = {'now': self.dt, 'str': '12345', 'int': 12345, 'list': [1, 2, 3, 4, 5]}
        self.list_with_dt = [self.dt, self.dt, self.dt]
        self.dict_with_list_of_dts = {'dict': {'list': self.list_with_dt, 'int': 10}}
        self.dict_no_dt = {'dict': {'list': [1, 2, 3, 'a', 'b', 'c'], 'int': 10}}

    def test_encode_decode(self):
        # want to make sure this doesn't throw an exception. Not sure
        # how to test for that
        objs = [self.dict_with_dt, self.dict_with_dt, self.dict_with_list_of_dts]
        strs = []
        try:
            for o in objs:
                strs.append(utils.json_codecs.encode_json(o))
        except Exception, ex:
            self.assertTrue(False, ex)
        self.assertEqual(len(objs), len(strs))

        for i in range(len(strs)):
            self.assertDictEqual(utils.json_codecs.decode_json(strs[i]), objs[i])
