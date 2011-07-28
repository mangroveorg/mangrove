# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mock import Mock
from mangrove.datastore.database import DatabaseManager
from mangrove.errors.MangroveException import FormModelDoesNotExistsException
from mangrove.transport.player import player
from mangrove.transport.player.parser import CsvParser
from mangrove.transport.player.player import CsvPlayer
from mangrove.transport.submissions import SubmissionHandler, SubmissionResponse


class TestCsvPlayer(unittest.TestCase):
    def _mock_short_code_generator(self):
        self.original_code_generator = player._generate_short_code_if_registration_form
        self.original_handler_for_reg_form = player.Player._handle_registration_form
        player._generate_short_code_if_registration_form = Mock(spec=player._generate_short_code_if_registration_form)
        player.Player._handle_registration_form = Mock(spec = player.Player._handle_registration_form)

    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        loc_tree = Mock()
        loc_tree.get_hierarchy_path.return_value = None
        self.submission_handler_mock = Mock(spec=SubmissionHandler)
        self.parser = CsvParser()

        self.csv_data = """
                                FORM_CODE,ID,BEDS,DIRECTOR,MEDS
                                CLF1,CL001,10,Dr. A,201
                                CLF1,CL002,11,Dr. B,202
                                CLF2,CL003,12,Dr. C,203
                                CLF1,CL004,13,Dr. D,204
                                CLF1,CL005,14,Dr. E,205
"""
        self._mock_short_code_generator()

        self.player = CsvPlayer(self.dbm, self.submission_handler_mock, self.parser, loc_tree)

    def tearDown(self):
        player._generate_short_code_if_registration_form = self.original_code_generator
        player.Player._handle_registration_form = self.original_handler_for_reg_form


    def test_should_import_csv_string(self):
        self.player.accept(self.csv_data)

        self.assertEqual(5, self.submission_handler_mock.accept.call_count)

    def test_should_process_next_submission_if_exception_with_prev(self):
        def expected_side_effect(*args, **kwargs):
            request = kwargs.get('request') or args[0]
            if request.form_code == 'clf2':
                raise FormModelDoesNotExistsException('')
            return SubmissionResponse(success=True, submission_id=1)

        self.submission_handler_mock.accept.side_effect = expected_side_effect

        response = self.player.accept(self.csv_data)
        self.assertEqual(5, len(response))
        self.assertEqual(False, response[2].success)

        success = len([index for index in response if index.success])
        total = len(response)
        self.assertEqual(4, success)
        self.assertEqual(5, total)
