from unittest.case import TestCase
from mock import patch, Mock
from mangrove.form_model.field import SelectField, GeoCodeField
from mangrove.transport.player.parser import XFormParser

class TestXFormParser(TestCase):
    def setUp(self):
        self.parser = XFormParser(Mock())

    def test_should_parse_input_and_return_submission_values(self):
        form_code = 'someFormCode'
        submission_values = {'data': {'form_code': form_code, 'q1': 'a b c', 'q2': 'lat long alt accuracy'}}
        expected_values = {'q1': 'abc', 'q2': 'lat,long'}
        with patch("mangrove.transport.player.parser.xmldict") as mock_xml_dict:
            mock_xml_dict.xml_to_dict.return_value = submission_values
            with patch("mangrove.transport.player.parser.get_form_model_by_code") as mock_get_form_model:
                mock_form_model = Mock()
                mock_form_model.fields = [SelectField('', 'q1', '', {'': ''}, Mock(), single_select_flag=False),
                                          GeoCodeField('', 'q2', '', {'': ''})]
                mock_get_form_model.return_value = mock_form_model
                self.assertEquals(self.parser.parse(submission_values), (form_code, expected_values))