# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mock import Mock
from mangrove.datastore.database import DatabaseManager
from mangrove.transport.player.player import CsvPlayer
from mangrove.transport.submissions import SubmissionHandler


class TestCsvPlayer(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.submission_handler_mock = Mock(spec=SubmissionHandler)

    def test_should_import_csv_string(self):
        csv_data = """
        FORM_CODE,ID,BEDS,DIRECTOR,MEDS
        CLF1,CL001,10,Dr. A,201
        CLF1,CL002,11,Dr. B,202
        CLF1,CL003,12,Dr. C,203
        CLF1,CL004,13,Dr. D,204
        CLF1,CL005,14,Dr. E,205
        """
        csv_player = CsvPlayer(self.dbm, self.submission_handler_mock)
        csv_player.accept(csv_data)

#        self.assertEqual(1,self.submission_handler_mock.accept.call_count)
