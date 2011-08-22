# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest import TestCase
from mangrove.errors.MangroveException import CSVParserInvalidHeaderFormatException
from mangrove.transport.player.parser import CsvParser

class TestCsvParser(TestCase):
    def test_should_parse_csv_string(self):
        csv_data = """FORM_CODE,ID,BEDS,DIRECTOR,MEDS
        CLF1, CL001, 11, Dr. A1,201
        CLF1,CL002,12,Dr. A2,202
        CLF1,CL003,13,Dr. A3,203
        CLF1,CL004,14,Dr. A4,204
        CLF1,CL005,15,Dr. A5,205"""

        csv_parser = CsvParser()
        results = csv_parser.parse(csv_data)

        self.assertEqual(5, len(results))

        for index, result in enumerate(results):
            form_code, values = results[index]
            self.assertEqual("clf1", form_code)
            offset = index + 1
            self.assertEqual(
                    {"id": "CL%03d" % (offset,), "beds": "%d" % (10 + offset,),
                     "director": "Dr. A%d" % (offset,),
                     "meds": "%d" % (200 + offset,)
                }, values)

    def test_should_parse_csv_string_with_partial_values(self):
        csv_data = """FORM_CODE,ID,BEDS,DIRECTOR,MEDS
        CLF1, CL001, 11, Dr. A1,201

        CLF1, CL001,, Dr. A1,201

        CLF1,CL002,12,"Dr. LastName,Firstname" """

        csv_parser = CsvParser()
        results = csv_parser.parse(csv_data)

        self.assertEqual(3, len(results))

        form_code, values = results[0]
        self.assertEqual("clf1", form_code)
        self.assertEqual(
                {"id": "CL001", "beds": "11",
                 "director": "Dr. A1",
                 "meds": "201"
            }, values)
        form_code, values = results[1]
        self.assertEqual("clf1", form_code)
        self.assertEqual(
                {"id": "CL001", "beds": "",
                 "director": "Dr. A1",
                 "meds": "201"
            }, values)

        form_code, values = results[2]
        self.assertEqual("clf1", form_code)
        self.assertEqual(
                {"id": "CL002", "beds": "12",
                 "director": "Dr. LastName,Firstname",
                 "meds": None
            }, values)

    def test_should_parse_csv_string_with_empty_lines(self):
        csv_data = """


        FORM_CODE,ID,BEDS,DIRECTOR,MEDS

        CLF1, CL001, 11, Dr. A1,201
        CLF1,CL002,12,Dr. A2,202

        CLF1,CL003,13,Dr. A3,203

        CLF1,CL004,14,Dr. A4,204
        CLF1,CL005,15,Dr. A5,205

        """

        csv_parser = CsvParser()
        results = csv_parser.parse(csv_data)

        self.assertEqual(5, len(results))

        self._assert_results(results)

    def test_should_raise_exception_for_invalid_format(self):
        empty_csv_data = """


     """

        csv_parser = CsvParser()
        with self.assertRaises(CSVParserInvalidHeaderFormatException):
            results = csv_parser.parse(empty_csv_data)

    def _assert_results(self, results):
        for index, result in enumerate(results):
            form_code, values = results[index]
            self.assertEqual("clf1", form_code)
            offset = index + 1
            self.assertEqual(
                    {"id": u"CL%03d" % (offset,), "beds": u"%d" % (10 + offset,),
                     "director": u"Dr. A%d" % (offset,),
                     "meds": u"%d" % (200 + offset,)
                }, values)

    def test_should_import_csv_string_with_trailing_commas(self):
        csv_data = """FORM_CODE,ID,BEDS,DIRECTOR,MEDS,
                                CLF1,CL001,11,Dr. A1,201,
                                CLF1,CL002,12,Dr. A2,202,
                                CLF1,CL003,13,Dr. A3,203,
                                CLF1,CL004,14,Dr. A4,204,
                                CLF1,CL005,15,Dr. A5,205,
        """
        csv_parser = CsvParser()
        results = csv_parser.parse(csv_data)

        self.assertEqual(5, len(results))

        self._assert_results(results)


    def test_should_import_csv_string_with_extra_field_values(self):
        csv_data = """FORM_CODE,ID,BEDS,DIRECTOR,MEDS
                                CLF1,CL001,11,Dr. A1,201
                                CLF1,CL002,12,Dr. A2,202,extra field
                                CLF1,CL003,13,Dr. A3,203,
                                CLF1,CL004,14,Dr. A4,204,extra field1, extra field 2
                                CLF1,CL005,15,Dr. A5,205,
        """
        csv_parser = CsvParser()
        results = csv_parser.parse(csv_data)

        self.assertEqual(5, len(results))

        self._assert_results(results)

    def test_should_raise_exception_if_empty_field_in_header(self):
        csv_data = """
                                FORM_CODE,ID,    ,DIRECTOR,MEDS
                                CLF1,CL001,11,Dr. A1,201
                                CLF1,CL002,12,Dr. A2,202
                                CLF1,CL003,13,Dr. A3,203
                                CLF1,CL004,14,Dr. A4,204
                                CLF1,CL005,15,Dr. A5,205
        """
        csv_parser = CsvParser()
        with self.assertRaises(CSVParserInvalidHeaderFormatException):
            csv_parser.parse(csv_data)