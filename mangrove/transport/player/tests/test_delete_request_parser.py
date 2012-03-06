# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from unittest import TestCase
from mangrove.errors.MangroveException import DeleteRequestParserInvalidFormatException, DeleteRequestParserWrongNumberOfAnswersException
from mangrove.transport.player.parser import DeleteRequestParser

class TestDeleteRequestParser(TestCase):

    def setUp(self):
        self.parser = DeleteRequestParser()
        self.entity_type_code = 'entity_type'
        self.entity_id_code = 'entity_id'
        self.command = 'delete'

    def test_should_assert_if_message_is_string(self):
        with self.assertRaises(AssertionError):
            self.parser.parse(dict())

    def test_should_validate_format(self):
        with self.assertRaises(DeleteRequestParserInvalidFormatException):
            self.parser.parse('blah.foo.bar')
        with self.assertRaises(DeleteRequestParserInvalidFormatException):
            self.parser.parse('blah')


    def test_should_return_command_and_values_from_message(self):
        entity_type = 'test_entity'
        entity_id = 'test1'

        command,values = self.parser.parse(' '.join([self.command, entity_type, entity_id]))
        self.assertEqual(self.command, command)
        self.assertEqual(2, len(values))

        self.assertTrue(self.entity_type_code in values)
        self.assertTrue(self.entity_id_code in values)

        self.assertEqual(entity_type, values[self.entity_type_code])
        self.assertEqual(entity_id, values[self.entity_id_code])

    def test_should_reject_message_with_incomplete_data(self):
        with self.assertRaises(DeleteRequestParserWrongNumberOfAnswersException):
            self.parser.parse('delete sss')

    def test_should_ignore_the_extra_tokens_in_message(self):
        entity_type = 'test_entity'
        entity_id = 'test1'
        command,values = self.parser.parse(' '.join([self.command, entity_type, entity_id])+' foo bar')
        self.assertEqual(2 , len(values))
        self.assertEqual(entity_type, values[self.entity_type_code])
        self.assertEqual(entity_id, values[self.entity_id_code])

    def test_should_take_care_of_the_extra_spaces_in_message(self):
        entity_type = 'test_entity'
        entity_id = 'test1'
        command,values = self.parser.parse('   delete    test_entity  test1     ')
        self.assertEqual(2 , len(values))
        self.assertEqual(entity_type, values[self.entity_type_code])
        self.assertEqual(entity_id, values[self.entity_id_code])














