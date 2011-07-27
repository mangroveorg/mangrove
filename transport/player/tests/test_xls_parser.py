# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest import TestCase
import os
import xlwt
from mangrove.errors.MangroveException import XlsParserInvalidHeaderFormatException
from mangrove.transport.player.parser import XlsParser

class TestXlsParser(TestCase):
    def setUp(self):
        data = """
                                FORM_CODE,ID,BEDS,DIRECTOR,MEDS

                                CLF1,CL001,10,Dr. A,201
                                CLF1,CL002,11,Dr. B,202

                                CLF2,CL003,12,Dr. C,203
                                CLF1,CL004,13,Dr. D,204
                                CLF1,CL005,14,Dr. E,205

"""
        self.file_name = "test.xls"
        wb = xlwt.Workbook()
        ws = wb.add_sheet('test')
        for row_number, row  in enumerate(data.split('\n')):
            for col_number, val in enumerate(row.split(',')):
                ws.write(row_number, col_number, val)
        wb.save(self.file_name)
        self.parser = XlsParser()

    def test_should_parse_xls_contents(self):
        input_file = open(self.file_name)
        submissions = self.parser.parse(input_file.read())
        self.assertEqual(5, len(submissions))
        form_code, values = submissions[0]
        self.assertEqual("clf1", form_code)
        self.assertEqual({"id": 'CL001', 'beds': '10', 'director': 'Dr. A', 'meds': '201'}, values)
        input_file.close()

    def test_should_raise_exception_for_invalid_format(self):
        data = """




"""
        os.remove(self.file_name)
        self.file_name = "test.xls"
        wb = xlwt.Workbook()
        ws = wb.add_sheet('test')
        for row_number, row  in enumerate(data.split('\n')):
            for col_number, val in enumerate(row.split(',')):
                ws.write(row_number, col_number, val)
        wb.save(self.file_name)
        input_file = open(self.file_name)
        with self.assertRaises(XlsParserInvalidHeaderFormatException):
            self.parser.parse(input_file.read())
        input_file.close()


    def tearDown(self):
        os.remove(self.file_name)