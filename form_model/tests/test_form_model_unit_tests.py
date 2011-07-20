# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType
from mangrove.errors.MangroveException import EntityQuestionCodeNotSubmitted
from mangrove.form_model.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import _construct_registration_form, FormModel, REGISTRATION_FORM_CODE
from mangrove.form_model.validation import NumericConstraint, TextConstraint


class TestFormModel(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.datadict_patcher = patch("mangrove.form_model.form_model.get_or_create_data_dict")
        self.datadict_mock = self.datadict_patcher.start()
        self.ddtype_mock = Mock(spec=DataDictType)
        self.datadict_mock.return_value = self.ddtype_mock

        q1 = TextField(name="entity_question", code="ID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=self.ddtype_mock)
        q2 = TextField(name="question1_Name", code="Q1", label="What is your name",
                              defaultValue="some default value", language="eng", length=TextConstraint(5, 10),
                              ddtype=self.ddtype_mock)
        q3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age",
                                 range=NumericConstraint(min=15, max=120), ddtype=self.ddtype_mock)
        q4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
                                options=[("RED", 1), ("YELLOW", 2)], ddtype=self.ddtype_mock)
        q5 = TextField(name="Desc", code="Q4", label="Description", ddtype=self.ddtype_mock)

        self.form_model = FormModel(self.dbm, entity_type=["XYZ"], name="aids", label="Aids form_model",
                                    form_code="1", type='survey', fields=[#        expected_short_code = "dog3"
#        self.assertEqual(response.short_code, expected_short_code)
#        b = get_by_short_code(self.dbm, expected_short_code, ["dog"])
#        self.assertEqual(b.short_code, expected_short_code)

                    q1, q2, q3, q4, q5])


    def tearDown(self):
        self.datadict_patcher.stop()

    def test_should_create_registration_form_mode(self):
        form = _construct_registration_form(self.dbm)
        self.assertEqual(7, len(form.fields))
        self.assertEqual(REGISTRATION_FORM_CODE, form.form_code)

    def test_registration_form_should_have_entity_type_field(self):
        form = _construct_registration_form(self.dbm)
        field = form.get_field_by_code("T")
        self.assertIsNotNone(field)


    def test_should_validate_for_valid_integer_value(self):
        answers = {"ID": "1", "Q2": "16"}
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertTrue(len(errors) == 0)

    def test_should_return_error_for_invalid_integer_value(self):
        answers = {"id": "1", "q2": "200"}
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertEqual(len(errors), 1)
        self.assertEqual({'q2': 'Answer 200 for question Q2 is greater than allowed.'}, errors)
        self.assertEqual({'ID': '1'}, cleaned_answers)

    def test_should_ignore_field_validation_if_the_answer_is_not_present(self):
        answers = {"id": "1", "q1": "Asif Momin", "q2": "20"}
        expected_result = {"ID": "1", "Q1": "Asif Momin", "Q2": 20}
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertTrue(len(errors) == 0)
        self.assertEqual(cleaned_answers, expected_result)

    def test_should_ignore_field_validation_if_the_answer_blank(self):
        answers = {"id": "1", "q1": "Asif Momin", "q2": ""}
        expected_result = {"ID": "1", "Q1": "Asif Momin"}
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
        self.assertEqual({'Q3': ['RED'], 'ID': '1'}, cleaned_answers)

    def test_should_strip_whitespaces(self):
        answers = {"id": "1", "q1": "   My Name", "q2": "  40 ", "q3": "a     ", "q4": "    "}
        expected_cleaned_data = {'ID': '1', "Q1": "My Name", "Q2": 40,
                                 "Q3": ["RED"]}
        cleaned_answers, errors = self.form_model._is_valid(answers)
        self.assertTrue(len(errors) == 0)
        self.assertEqual(0, len(errors))
        self.assertEqual(cleaned_answers, expected_cleaned_data)

    def test_give_error_for_no_entity_short_code(self):
        with self.assertRaises(EntityQuestionCodeNotSubmitted):
            answers = {"Q2": "10"}
            self.form_model._is_valid(answers)

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
                              defaultValue="some default value", language="eng", length=TextConstraint(5, 10),
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

    def test_create_form_submission_with_entity_type_as_lowercase_list_of_string(self):
        answers = {"s": "1", "t": "Reporter"}
        registration_form = _construct_registration_form(self.dbm)
        form_submission = registration_form.validate_submission(answers)
        self.assertEqual(["reporter"], form_submission.entity_type)

        answers = {"s": "1", "t": ["Reporter"]}
        form_submission = registration_form.validate_submission(answers)
        self.assertEqual(["reporter"], form_submission.entity_type)

