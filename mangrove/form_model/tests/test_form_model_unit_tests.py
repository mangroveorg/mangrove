# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from collections import OrderedDict
import unittest
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.field import TextField, IntegerField, SelectField, DateField
from mangrove.form_model.form_model import FormModel
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint


class TestFormModel(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.ddtype_mock = Mock(spec=DataDictType)

        q1 = TextField(name="entity_question", code="ID", label="What is associated entity",
                       language="eng", entity_question_flag=True, ddtype=self.ddtype_mock)
        q2 = TextField(name="question1_Name", code="Q1", label="What is your name",
                       defaultValue="some default value", language="eng", constraints=[TextLengthConstraint(5, 10)],
                       ddtype=self.ddtype_mock, required=False)
        q3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age",
                          constraints=[NumericRangeConstraint(min=15, max=120)], ddtype=self.ddtype_mock, required=False)
        q4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
                         options=[("RED", 1), ("YELLOW", 2)], ddtype=self.ddtype_mock, required=False)
        q5 = TextField(name="Desc", code="Q4", label="Description", ddtype=self.ddtype_mock, required=False)
        self.event_time_field_code = "Q6"
        q6 = DateField(name="Event time", code=self.event_time_field_code, label="Event time field", date_format = "%m.%d.%Y",ddtype=self.ddtype_mock, required=False,event_time_field_flag=True)

        self.form_model = FormModel(self.dbm, entity_type=["XYZ"], name="aids", label="Aids form_model",
                                    form_code="1", type='survey', fields=[q1, q2, q3, q4, q5,q6])


    def tearDown(self):
        pass
    
    def test_should_validate_for_valid_integer_value(self):
        answers = {"ID": "1", "Q2": "16"}
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertTrue(len(errors) == 0)

    def test_should_return_error_for_invalid_integer_value(self):
        answers = {"id": "1", "q2": "200"}
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertEqual(len(errors), 1)
        self.assertEqual({'q2': 'Answer 200 for question Q2 is greater than allowed.'}, errors)
        self.assertEqual(OrderedDict([('ID', '1')]), cleaned_answers)

    def test_should_ignore_field_validation_if_the_answer_is_not_present(self):
        answers = {"id": "1", "q1": "Asif Momin", "q2": "20"}
        expected_result = OrderedDict([('Q1', 'Asif Momin'), ('Q2', 20.0), ('ID', '1')])
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertTrue(len(errors) == 0)
        self.assertEqual(cleaned_answers, expected_result)

    def test_should_ignore_field_validation_if_the_answer_blank(self):
        answers = {"id": "1", "q1": "Asif Momin", "q2": ""}
        expected_result = OrderedDict([('Q1', 'Asif Momin'), ('ID', '1')])
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertTrue(len(errors) == 0)
        self.assertEqual(cleaned_answers, expected_result)

    def test_should_validate_for_valid_text_value(self):
        answers = {"ID": "1", "Q1": "Asif Momin"}
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertTrue(len(errors) == 0)

    def test_should_return_errors_for_invalid_text_and_integer(self):
        answers = {"id": "1", "q1": "Asif", "q2": "200", "q3": "a"}
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertEqual(len(errors), 2)
        self.assertEqual({'q1': 'Answer Asif for question Q1 is shorter than allowed.',
                          'q2': 'Answer 200 for question Q2 is greater than allowed.'}, errors)
        self.assertEqual(OrderedDict([('Q3', ['RED']), ('ID', '1')]), cleaned_answers)

    def test_should_strip_whitespaces(self):
        answers = {"id": "1", "q1": "   My Name", "q2": "  40 ", "q3": "a     ", "q4": "    "}
        expected_cleaned_data = OrderedDict([('Q1', 'My Name'), ('Q3', ['RED']), ('Q2', 40.0), ('ID', '1')])
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertTrue(len(errors) == 0)
        self.assertEqual(0, len(errors))
        self.assertEqual(cleaned_answers, expected_cleaned_data)
        
    def test_should_validate_field_case_insensitive(self):
        answers = {"Id": "1", "Q1": "Asif Momin", "q2": "40"}
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertTrue(len(errors) == 0)
        self.assertEqual({}, errors)


    def test_should_return_valid_form_submission(self):
        answers = {"ID": "1", "Q2": "16"}
        form_submission = self.form_model.validate_submission(answers)
        self.assertTrue(form_submission.is_valid)
        self.assertEqual("1", form_submission.short_code)
        self.assertEqual({"Q2": 16.0, 'ID': '1'}, form_submission.cleaned_data)
        self.assertEqual(0, len(form_submission.errors))

    def test_should_return_invalid_form_submission(self):
        answers = {"ID": "1", "Q2": "non number value"}
        form_submission = self.form_model.validate_submission(answers)
        self.assertFalse(form_submission.is_valid)
        self.assertEqual("1", form_submission.short_code)
        self.assertEqual({'ID': '1'}, form_submission.cleaned_data)
        self.assertEqual(1, len(form_submission.errors))

    def test_should_assert_activity_report(self):
        question1 = TextField(name="question1_Name", code="Q1", label="What is your name",
                              defaultValue="some default value", language="eng",
                              constraints=[TextLengthConstraint(5, 10)],
                              ddtype=self.ddtype_mock)
        activity_report = FormModel(self.dbm, entity_type=["reporter"], name="aids", label="Aids form_model",
                                    form_code="1", type='survey', fields=[question1])
        self.assertTrue(activity_report.entity_defaults_to_reporter())

    def test_form_model_is_active_when_created(self):
        self.assertTrue(self.form_model.is_active())

    def test_should_be_able_to_deactivate_the_form_model(self):
        self.form_model.deactivate()
        self.assertFalse(self.form_model.is_active())

    def test_should_be_able_to_activate_the_form_model(self):
        self.form_model.deactivate()
        self.assertFalse(self.form_model.is_active())
        self.form_model.activate()
        self.assertTrue(self.form_model.is_active())

    def test_should_be_able_to_put_the_form_model_in_test_mode(self):
        self.form_model.set_test_mode()
        self.assertTrue(self.form_model.is_in_test_mode())

    def _case_insensitive_lookup(self, values, code):
        for fieldcode in values:
            if fieldcode.lower() == code.lower():
                return values[fieldcode]
        return None


    def test_should_bind_form_to_submission(self):
        answers = {"ID": "1", "q1": "Asif", "q2": "200", "q3": "1", "q4": ""}
        self.form_model.bind(answers)
        self.assertEqual(answers, self.form_model.submission)
        for field in self.form_model.fields:
            self.assertEqual(self._case_insensitive_lookup(answers, field.code), field.value,
                             "No match for field %s" % (field.code,))

    def test_should_set_error_on_field_validation_failure(self):
        answers = {"id": "1", "q1": "ab", "q2": "200"}
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertEqual(len(errors), 2)
        self.assertEqual(['Answer 200 for question Q2 is greater than allowed.'], self.form_model.get_field_by_code(
            "q2").errors)
        self.assertEqual(['Answer ab for question Q1 is shorter than allowed.'], self.form_model.get_field_by_code(
            "q1").errors)

    def test_should_not_set_error_if_validation_success(self):
        answers = {"id": "1", "q1": "abcdef", "q2": "100"}
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertEqual(len(errors), 0)
        for field in self.form_model.fields:
            self.assertEqual([], field.errors)


    def test_should_get_event_time_question(self):
        self.assertEqual(self.event_time_field_code,self.form_model.event_time_question.code)















