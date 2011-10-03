# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mock import Mock
from mangrove.datastore.datadict import DataDictType
from mangrove.errors.MangroveException import EntityQuestionCodeNotSubmitted
from mangrove.form_model.field import TextField
from mangrove.form_model.validators import MandatoryValidator, EntityQuestionAnsweredValidator

class TestMandatoryValidator(unittest.TestCase):

    def setUp(self):
        self.validator = MandatoryValidator()
        self.field1 = TextField('a','a','a',Mock(spec=DataDictType))
        self.field2 = TextField('b','b','b',Mock(spec=DataDictType), required=False)
        self.field3 = TextField('c','c','c',Mock(spec=DataDictType))
        self.field4 = TextField('d','d','d',Mock(spec=DataDictType))
        self.fields = [self.field1,self.field2,self.field3,self.field4]

    def tearDown(self):
        pass

    def test_should_find_mandatory_fields(self):
        mandatory_field_list = self.validator.get_mandatory_fields(self.fields)
        self.assertEqual(3,len(mandatory_field_list))

    def test_should_return_error_dict_if_mandatory_field_answer_not_present(self):
        values = dict(a='test1',b='test2',d='test4')
        errors = self.validator.validate(values,self.fields)
        self.assertEqual(1, len(errors.keys()))
        self.assertTrue('c' in errors.keys())
        self.assertFalse('a' in errors.keys())

class TestEntityQuestionNotAnsweredValidator(unittest.TestCase):

    def setUp(self):
        self.validator = EntityQuestionAnsweredValidator()
        self.field1 = TextField('a','a','a',Mock(spec=DataDictType), entity_question_flag=True)
        self.field2 = TextField('b','b','b',Mock(spec=DataDictType), required=False)
        self.field3 = TextField('c','c','c',Mock(spec=DataDictType))
        self.fields = [self.field1,self.field2,self.field3]

    def test_should_raise_exception_if_entity_question_not_answered(self):
        values = dict(b='test2',c='test4')
        with self.assertRaises(EntityQuestionCodeNotSubmitted):
            self.validator.validate(values,self.fields)

    def test_should_not_raise_exception_if_entity_question_is_answered(self):
        values = dict(b='test2',c='test4', a='test1')
        self.validator.validate(values,self.fields)

