# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest import TestCase
import os
import xlwt
from mangrove.errors.MangroveException import XlsParserInvalidHeaderFormatException
from mangrove.transport.player.parser import XlsParser

class TestXlsParser(TestCase):
    def _write_to_xls(self, data):
        self.file_name = "test.xls"
        wb = xlwt.Workbook()
        ws = wb.add_sheet('test')
        for row_number, row  in enumerate(data.split('\n')):
            for col_number, val in enumerate(row.split(',')):
                ws.write(row_number, col_number, val)
        wb.save(self.file_name)

    def setUp(self):
        data = """
                                                                 FORM_CODE,ID,BEDS,DIRECTOR,MEDS

                                                                 CLF1,CL001,10,Dr. A,201
                                                                 CLF1,CL002,11,Dr. B,202

                                                                 CLF2,CL003,12,Dr. C,203
                                                                 CLF1,CL004,13,Dr. D,204
                                                                 CLF1,CL005,14,Dr. E,205

                                 """
        self._write_to_xls(data)
        self.parser = XlsParser()

    def test_should_parse_xls_contents(self):
        with open(self.file_name) as input_file:
            submissions = self.parser.parse(input_file.read())
            self.assertEqual(5, len(submissions))
            form_code, values = submissions[0]
            self.assertEqual(u"clf1", form_code)
            self.assertEqual({u"id": u'CL001', u'beds': u'10', u'director': u'Dr. A', u'meds': u'201'}, values)

    def test_should_raise_exception_for_invalid_format(self):
        data = """




                                 """
        self._write_to_xls(data)
        with open(self.file_name) as input_file:
            with self.assertRaises(XlsParserInvalidHeaderFormatException):
                self.parser.parse(input_file.read())

    def test_should_parse_xls_contents_with_extra_field_values(self):
        data = """
                                                FORM_CODE,ID,BEDS,DIRECTOR,MEDS
                                                CLF1,CL001,10,Dr. A,201
                                                CLF1,CL002,11,Dr. B,202, extra field
                                                CLF2,CL003,12,Dr. C,203
                                                CLF1,CL004,13,Dr. D,204, extra1, extra 2
                                                CLF1,CL005,14,Dr. E,205

                                    """
        self._write_to_xls(data)
        with open(self.file_name) as input_file:
            submissions = self.parser.parse(input_file.read())
            self.assertEqual(5, len(submissions))
            form_code, values = submissions[1]
            self.assertEqual("clf1", form_code)
            self.assertEqual({u"id": u'CL002', u'beds': u'11', u'director': u'Dr. B', u'meds': u'202'}, values)
            form_code, values = submissions[3]
            self.assertEqual("clf1", form_code)
            self.assertEqual({u"id": u'CL004', u'beds': u'13', u'director': u'Dr. D', u'meds': u'204'}, values)

    def test_should_parse_xls_contents_less_field_values_than_header(self):
        data = """
                                                FORM_CODE,ID,BEDS,DIRECTOR,MEDS
                                                CLF1,CL001,10,Dr. A,201
                                                CLF1,CL002,,Dr. B,202
                                                CLF2,CL003,12,Dr. C,203
                                                CLF1,CL004,13,Dr. D,204
                                                CLF1,CL005,14,Dr. E,205

                                    """
        self._write_to_xls(data)
        with open(self.file_name) as input_file:
            submissions = self.parser.parse(input_file.read())
            self.assertEqual(5, len(submissions))
            form_code, values = submissions[1]
            self.assertEqual("clf1", form_code)
            self.assertEqual({u"id": u'CL002', u'beds': u'', u'director': u'Dr. B', u'meds': u'202'}, values)

    def test_should_convert_int_to_long_before_converting_to_unicode_in_clean(self):
        row = ['test_info', 2.66123321435e+11, 'testing']
        expected_value = [u'test_info', u'266123321435', u'testing']
        actual_value = self.parser._clean(row)
        self.assertEqual(expected_value, actual_value)

    def tearDown(self):
        os.remove(self.file_name)
        pass
