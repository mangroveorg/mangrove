from unittest.case import TestCase
from mock import patch, Mock
from mangrove.form_model.field import SelectField, GeoCodeField, DateField, IntegerField
from mangrove.transport.player.parser import XFormParser

class TestXFormParser(TestCase):
    def setUp(self):
        self.parser = XFormParser(Mock())

    def test_should_parse_input_and_return_submission_values(self):
        form_code = 'someFormCode'
        submission_values = {
            'data': {'form_code': form_code, 'q1': 'a b c', 'q2': 'lat long alt accuracy', 'q3': '1012-01-23', 'q4':'1.0'}}
        expected_values = {'q1': 'abc', 'q2': 'lat,long', 'q3': '01.1012', 'q4': '1'}
        with patch("mangrove.transport.player.parser.xmldict") as mock_xml_dict:
            mock_xml_dict.xml_to_dict.return_value = submission_values
            with patch("mangrove.transport.player.parser.get_form_model_by_code") as mock_get_form_model:
                ddtype_mock = Mock()
                mock_form_model = ddtype_mock
                mock_form_model.fields = [SelectField('', 'q1', '', {'': ''}, ddtype_mock, single_select_flag=False),
                                          GeoCodeField('', 'q2', '', {'': ''}),
                                          DateField('', 'q3', '', 'mm.yyyy', ddtype_mock),
                                          IntegerField('', 'q4', '', ddtype_mock)]
                mock_get_form_model.return_value = mock_form_model
                self.assertEquals(self.parser.parse(submission_values), (form_code, expected_values))