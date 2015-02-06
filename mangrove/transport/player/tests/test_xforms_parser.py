# coding=utf-8
from unittest.case import TestCase
from mock import patch, Mock
from mangrove.form_model.field import SelectField, GeoCodeField, DateField, IntegerField, TextField, FieldSet, \
    PhotoField, AudioField, VideoField
from mangrove.transport.player.parser import XFormParser


class TestXFormParser(TestCase):
    def setUp(self):
        self.parser = XFormParser(Mock())

    def test_should_parse_input_and_return_submission_values(self):
        form_code = 'someFormCode'
        submission_values = {
            'data': {'form_code': form_code, 'q1': 'a b c', 'q2': 'lat long alt accuracy', 'q3': '1012-01-23',
                     'q4': '1'}}
        expected_values = {'q1': 'a b c', 'q2': 'lat,long', 'q3': '01.1012', 'q4': '1'}
        with patch("mangrove.transport.player.parser.xmltodict") as mock_xml_dict:
            mock_xml_dict.parse.return_value = submission_values
            with patch("mangrove.transport.player.parser.get_form_model_by_code") as mock_get_form_model:
                mock_form_model = Mock()
                mock_form_model.fields = [SelectField('', 'q1', '', {'': ''}, single_select_flag=False),
                                          GeoCodeField('', 'q2', '', {'': ''}),
                                          DateField('', 'q3', '', 'mm.yyyy'),
                                          IntegerField('', 'q4', '')]
                mock_get_form_model.return_value = mock_form_model
                self.assertEquals(self.parser.parse(submission_values), (form_code, expected_values))

    def test_should_parse_submission_values_with_accented_characters(self):
        submission_data = u'''
        <hindimai-055>
            <name>नाम asd</name>
            <form_code>055</form_code>
        </hindimai-055>
        '''
        expected_values = {'name': u'नाम asd'}
        with patch("mangrove.transport.player.parser.get_form_model_by_code") as mock_get_form_model:
            mock_form_model = Mock()
            mock_form_model.fields = [TextField('', 'name', '')]
            mock_get_form_model.return_value = mock_form_model

            self.assertEquals(self.parser.parse(submission_data), ('055', expected_values))

    def test_should_accept_submission_with_empty_fields(self):
        submission_data = u'''
        <hindimai-055>
            <name/>
            <age/>
            <dob/>
            <location/>
            <form_code>055</form_code>
        </hindimai-055>
        '''
        expected_values = {'name': None, 'age': None, 'dob': None, 'location': None}
        with patch("mangrove.transport.player.parser.get_form_model_by_code") as mock_get_form_model:
            mock_form_model = Mock()
            mock_form_model.fields = [TextField('', 'name', ''),
                                      GeoCodeField('', 'location', '', {'': ''}),
                                      DateField('', 'dob', '', 'mm.yyyy'),
                                      IntegerField('', 'age', '')]
            mock_get_form_model.return_value = mock_form_model

            self.assertEquals(self.parser.parse(submission_data), ('055', expected_values))

    def test_should_accept_submission_with_media_fields(self):
        submission_data = u'''
        <hindimai-055>
            <image type="file">image.png</image>
            <audio type="file">audio.mp3</audio>
            <video type="file">video.mp4</video>
            <form_code>055</form_code>
        </hindimai-055>
        '''
        expected_values = {'image': "image.png", 'audio': "audio.mp3", 'video': "video.mp4"}
        with patch("mangrove.transport.player.parser.get_form_model_by_code") as mock_get_form_model:
            mock_form_model = Mock()
            mock_form_model.fields = [PhotoField('', 'image', ''),
                                      AudioField('', 'audio', ''),
                                      VideoField('', 'video', '')]
            mock_get_form_model.return_value = mock_form_model

            self.assertEquals(self.parser.parse(submission_data), ('055', expected_values))

    def test_should_accept_submission_with_repeat_fields(self):
        submission_data = u'''
        <hindimai-055>
            <familyname>singh</familyname>
            <family>
                <name>नाम asd</name>
                <age>12</age>
            </family>
            <family>
                <name>tommy</name>
                <age>15</age>
            </family>
            <form_code>055</form_code>
        </hindimai-055>
        '''
        expected_values = {'familyname': 'singh',
                           'family': [{'name': u'नाम asd', 'age': '12'}, {'name': 'tommy', 'age': '15'}]}
        with patch("mangrove.transport.player.parser.get_form_model_by_code") as mock_get_form_model:
            mock_form_model = Mock()
            mock_form_model.fields = [TextField('', 'familyname', ''),
                                      FieldSet('', 'family', '',
                                               field_set=[TextField('', 'name', ''), IntegerField('', 'age', '')])]
            mock_get_form_model.return_value = mock_form_model

            self.assertEquals(self.parser.parse(submission_data), ('055', expected_values))