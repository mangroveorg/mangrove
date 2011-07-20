# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
import os

from mangrove.utils.spreadsheets import CsvReader


class TestCsvReader(unittest.TestCase):
    def setUp(self):
        file_name = 'test.csv'
        dirname = os.path.dirname(__file__)
        abspath = os.path.abspath(dirname)
        file_path = os.path.join(abspath, file_name)
        self.csv_reader = CsvReader(file_path)

    def test_iteritems(self):
        expected_list = [
                {
                'one': '1',
                'two': '2',
                'three': '3',
                },
                 ]
        actual_list = list(self.csv_reader.iter_dicts())
        self.assertEquals(expected_list, actual_list)
