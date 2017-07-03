from unittest.case import TestCase
from mangrove.transport.repository.reporters import find_reporter_entity, find_reporters_by_from_number
from mock import patch, Mock

class TestFindReporters(TestCase):

    def test_should_return_even_there_is_plus_leading_to_incoming_number(self):
        def return_x(dbm, number):
            return [number]
        
        with patch("mangrove.transport.repository.reporters.find_reporters_by_from_number") as find_ds_by_from:
            find_ds_by_from.side_effect = return_x

            reporter = find_reporter_entity(Mock(), "+23242432")
            self.assertEqual(reporter, "23242432")
        