# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from unittest import TestCase
from mangrove.transport.player.parser import WebParser


class TestWebParser(TestCase):
    def setUp(self):
        self.web_parser = WebParser()

    def test_should_return_form_code_and_message_as_dict(self):
        message = {'form_code': 'X1', 'q1': 'a1', 'q2': 'a2'}
        form_code, values = self.web_parser.parse(message)
        self.assertEquals(form_code, 'X1')
        self.assertEquals(values, {'q1': 'a1', 'q2': 'a2'})

    def test_should_allow_none_values(self):
        message = {'form_code': 'X1', 'q1': 'a1', 'q2': None}
        form_code, values = self.web_parser.parse(message)
        self.assertEquals(form_code, 'X1')
        self.assertEquals(values, {'q1': 'a1', 'q2': None})

    def test_should_allow_empty_values(self):
        message = {'form_code': 'X1', 'q1': 'a1', 'q2': ""}
        form_code, values = self.web_parser.parse(message)
        self.assertEquals(form_code, 'X1')
        self.assertEquals(values, {'q1': 'a1', 'q2': ""})

    def test_should_allow_integer_values(self):
        message = {'form_code': 'X1','q2': 21}
        form_code, values = self.web_parser.parse(message)
        self.assertEquals(values, {'q2': "21"})

    def test_should_allow_float_values(self):
        message = {'form_code': 'X1','q2': 21.5}
        form_code, values = self.web_parser.parse(message)
        self.assertEquals(values, {'q2': "21.5"})

    def test_should_convert_list_value_to_string(self):
        message = {'form_code': 'X1', 'q1': ['a1', 'a2'], 'q2': [""], 'q3': []}
        form_code, values = self.web_parser.parse(message)
        self.assertEquals(form_code, 'X1')
        self.assertEquals(values, {'q1': 'a1a2', 'q2': "", 'q3': ''})

    def test_should_remove_csrf_token_if_it_exists(self):
        message = {'form_code': 'X1', 'q1': ['a1', 'a2'], 'q2': [""], 'q3': [],
                   'csrfmiddlewaretoken': 'some csrf token'}
        form_code, values = self.web_parser.parse(message)
        self.assertEquals(form_code, 'X1')
        self.assertEquals(values, {'q1': 'a1a2', 'q2': "", 'q3': ''})














