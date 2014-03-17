from collections import OrderedDict
import unittest
from mock import Mock, patch
from mangrove.datastore.documents import FormModelDocument
from mangrove.datastore.database import DatabaseManager, DataObject
from mangrove.form_model.field import TextField, IntegerField, SelectField, DateField, GeoCodeField, UniqueIdField
# from mangrove.form_model.form_model import get_form_model_by_entity_type
from mangrove.form_model.form_model import FormModel, get_form_model_by_code, EntityFormModel, get_form_model_by_entity_type
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint
from mangrove.form_model.validators import MandatoryValidator, UniqueIdExistsValidator


class TestFormModel(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)

        q1 = UniqueIdField('clinic', name="entity_question", code="ID", label="What is associated entity")
        q2 = TextField(name="question1_Name", code="Q1", label="What is your name",
                       defaultValue="some default value", constraints=[TextLengthConstraint(5, 10)],
                       required=False)
        q3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age",
                          constraints=[NumericRangeConstraint(min=15, max=120)], required=False)
        q4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
                         options=[("RED", 1), ("YELLOW", 2)], required=False)
        q5 = TextField(name="Desc", code="Q4", label="Description", required=False)
        self.event_time_field_code = "Q6"
        q6 = DateField(name="Event time", code=self.event_time_field_code, label="Event time field",
                       date_format="%m.%d.%Y", required=False, event_time_field_flag=True)
        q7 = GeoCodeField(name="My Location", code="loc", label="Geo Location Field", required=False)
        self.form_model = FormModel(self.dbm, name="aids", label="Aids form_model",
                                    form_code="1", type='survey', fields=[q1, q2, q3, q4, q5, q6, q7])

        self.form_model_patch = patch('mangrove.form_model.form_model.FormModel')
        self.form_model_document_patch = patch('mangrove.form_model.form_model.FormModelDocument')

    def tearDown(self):
        try:
            self.form_model_patch.stop()
            self.form_model_document_patch.stop()
        except Exception:
            pass

    def test_should_validate_for_valid_integer_value(self):
        answers = {"ID": "1", "Q2": "16"}
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertTrue(len(errors) == 0)

    def test_should_return_error_for_invalid_integer_value(self):
        answers = {"id": "1", "Q2": "200"}
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertEqual(len(errors), 1)
        self.assertEqual({'Q2': "Answer 200 for question Q2 is greater than allowed."}, errors)
        self.assertEqual(OrderedDict([('ID', '1')]), cleaned_answers)

    def test_should_return_error_if_exceeding_value_of_the_word_field_limit(self):
        answers = {"id": "1", "Q1": "TextThatLongerThanAllowed"}
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertEqual(len(errors), 1)
        self.assertEqual({'Q1': 'Answer TextThatLongerThanAllowed for question Q1 is longer than allowed.'}, errors)
        self.assertEqual(OrderedDict([('ID', '1')]), cleaned_answers)

    def test_should_return_error_if_answering_with_invalid_geo_format(self):
        answers = {"id": "1", "loc": "127.178057 -78.007789"}
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertEqual(len(errors), 1)
        self.assertEqual({'loc': 'Invalid GPS value.'}, errors)
        self.assertEqual(OrderedDict([('ID', '1')]), cleaned_answers)


    def test_should_ignore_field_validation_if_the_answer_is_not_present(self):
        answers = {"id": "1", "q1": "Asif Momin", "q2": "20"}
        expected_result = OrderedDict([('Q1', 'Asif Momin'), ('Q2', 20.0), ('ID', '1')])
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertTrue(len(errors) == 0)
        self.assertEqual(cleaned_answers, expected_result)

    def test_should_ignore_field_validation_if_the_answer_blank(self):
        answers = {"id": "1", "q1": "Asif Momin", "q2": ""}
        expected_result = OrderedDict([('Q1', 'Asif Momin'), ('ID', '1')])
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertTrue(len(errors) == 0)
        self.assertEqual(cleaned_answers, expected_result)

    def test_should_validate_for_valid_text_value(self):
        answers = {"ID": "1", "Q1": "Asif Momin"}
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertTrue(len(errors) == 0)

    def test_should_return_errors_for_invalid_text_and_integer(self):
        answers = {"id": "1", "Q1": "Asif", "Q2": "200", "q3": "a"}
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertEqual(len(errors), 2)
        self.assertEqual({'Q1': 'Answer Asif for question Q1 is shorter than allowed.',
                          'Q2': "Answer 200 for question Q2 is greater than allowed."}, errors)
        self.assertEqual(OrderedDict([('Q3', ['RED']), ('ID', '1')]), cleaned_answers)

    def test_should_strip_whitespaces(self):
        answers = {"id": "1", "q1": "   My Name", "q2": "  40 ", "q3": "a     ", "q4": "    "}
        expected_cleaned_data = OrderedDict([('Q1', 'My Name'), ('Q3', ['RED']), ('Q2', 40.0), ('ID', '1')])
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertTrue(len(errors) == 0)
        self.assertEqual(0, len(errors))
        self.assertEqual(cleaned_answers, expected_cleaned_data)

    def test_should_validate_field_case_insensitive(self):
        answers = {"Id": "1", "Q1": "Asif Momin", "q2": "40"}
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertTrue(len(errors) == 0)
        self.assertEqual({}, errors)


    def test_should_return_valid_form_submission(self):
        answers = {"ID": "1", "Q2": "16"}
        cleaned_data, errors = self.form_model.validate_submission(answers)
        self.assertEqual({"Q2": 16.0, 'ID': '1'}, cleaned_data)
        self.assertEqual(0, len(errors))

    def test_should_return_invalid_form_submission(self):
        answers = {"ID": "1", "Q2": "non number value"}
        cleaned_data, errors = self.form_model.validate_submission(answers)
        self.assertEqual({'ID': '1'}, cleaned_data)
        self.assertEqual(1, len(errors))

    def test_should_give_back_unique_id_field(self):
        question1 = UniqueIdField('entity_type', name="question1_Name", code="Q1", label="What is your name",
                                  defaultValue="some default value")
        activity_report = FormModel(self.dbm, name="aids", label="Aids form_model",
                                    form_code="1", type='survey', fields=[question1])
        self.assertIsNotNone(activity_report.unique_id_field)


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
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertEqual(len(errors), 2)
        self.assertEqual(["Answer 200 for question Q2 is greater than allowed."], self.form_model._get_field_by_code(
            "q2").errors)
        self.assertEqual(['Answer ab for question Q1 is shorter than allowed.'], self.form_model._get_field_by_code(
            "q1").errors)

    def test_should_not_set_error_if_validation_success(self):
        answers = {"id": "1", "q1": "abcdef", "q2": "100"}
        cleaned_answers, errors = self.form_model.validate_submission(answers)
        self.assertEqual(len(errors), 0)
        for field in self.form_model.fields:
            self.assertEqual([], field.errors)


    def test_should_get_event_time_question(self):
        self.assertEqual(self.event_time_field_code, self.form_model.event_time_question.code)

    # def test_should_check_if_proper_database_manager_passed_for_get_registration_form(self):
    #     with self.assertRaises(AssertionError):
    #         get_form_model_by_entity_type(Mock(), Mock())
    #
    # def test_should_check_if_entity_type_is_sequesnce_for_get_registration_form(self):
    #     with self.assertRaises(AssertionError):
    #         get_form_model_by_entity_type(Mock(spec=DatabaseManager), 'clinic')
    #
    # def test_return_none_if_registration_form_model_for_an_entity_does_not_exist(self):
    #     manager_stub = DatabaseManagerStub()
    #     manager_stub.view.registration_form_model_by_entity_type.return_value = []
    #     self.assertIsNone(get_form_model_by_entity_type(manager_stub, ["XYZ"]))

    # def test_should_return_registration_form_model_if_found_for_an_entity(self):
    #     manager_stub = DatabaseManagerStub()
    #     document = {'foo':'bar'}
    #     manager_stub.view.registration_form_model_by_entity_type.return_value = [
    #             {"id": "tes_id", "key": ["test"], "value": None,
    #              'doc': document}]
    #     mock_form_instance = Mock(FormModel)
    #     mock_form_document_instance = Mock(FormModelDocument)
    #
    #     form_model_mock = self.form_model_patch.start()
    #     form_model_mock.new_from_doc.return_value = mock_form_instance
    #
    #     form_model_document_mock = self.form_model_document_patch.start()
    #     form_model_document_mock.wrap.return_value = mock_form_document_instance
    #
    #     reg_form_model = get_form_model_by_entity_type(manager_stub, ['test'])
    #
    #     self.assertEqual(mock_form_instance, reg_form_model)
    #     manager_stub.view.registration_form_model_by_entity_type.assert_called_once_with(key=['test'],
    #         include_docs=True)
    #     self.assertEqual(1, form_model_mock.new_from_doc.call_count)
    #     form_model_document_mock.wrap.assert_called_once_with(document)

    def test_should_return_choice_fields(self):
        self.assertEquals(self.form_model.choice_fields[0].code, "Q3")
        self.assertEquals(len(self.form_model.choice_fields), 1)

    def test_should_return_dictionary_of_question_code_and_label(self):
        dictionary = self.form_model.get_field_code_label_dict()
        codes = dictionary.keys()
        values = dictionary.values()
        self.assertEquals(7, dictionary.__len__())
        self.assertEquals(["ID", "Q1", "Q2", "Q3", "Q4", "Q6", "loc"].sort(), codes.sort())
        self.assertEquals(["What is associated entity",
                           "What is your name",
                           "What is your Father's Age",
                           "What is your favourite color",
                           "Description",
                           "Event time field",
                           "Geo Location Field"].sort(), values.sort())

    def test_should_add_validator_to_form_model_if_not_already_present(self):
        self.form_model.validators = [MandatoryValidator()]
        self.form_model.add_validator(UniqueIdExistsValidator)
        self.assertEquals(len(self.form_model.validators), 2)

    def test_should_not_add_validator_to_form_model_if_already_present(self):
        self.form_model.validators = [MandatoryValidator(), UniqueIdExistsValidator()]
        self.form_model.add_validator(UniqueIdExistsValidator)
        self.assertEquals(len(self.form_model.validators), 2)

    def test_should_remove_validator_from_form_model(self):
        self.form_model.validators = [MandatoryValidator(), UniqueIdExistsValidator()]
        self.form_model.remove_validator(UniqueIdExistsValidator)
        self.assertEquals(len(self.form_model.validators), 1)

    def test_should_get_entity_form_model_if_registration_flag_is_set(self):
        with patch('mangrove.form_model.form_model.get_cache_manager') as get_cache_manager:
            with patch('mangrove.form_model.form_model.get_form_model_cache_key') as get_form_model_cache_key:
                get_cache_manager.return_value = {'cache_key': {'is_registration_model': True}}
                get_form_model_cache_key.return_value = 'cache_key'
                form_model = get_form_model_by_code(self.dbm, 'code')
                self.assertIsInstance(form_model, EntityFormModel)

    def test_should_get_submission_form_model_if_registration_flag_is_false(self):
        with patch('mangrove.form_model.form_model.get_cache_manager') as get_cache_manager:
            with patch('mangrove.form_model.form_model.get_form_model_cache_key') as get_form_model_cache_key:
                get_cache_manager.return_value = {'cache_key': {'is_registration_model': False}}
                get_form_model_cache_key.return_value = 'cache_key'
                form_model = get_form_model_by_code(self.dbm, 'code')
                self.assertIsInstance(form_model, FormModel)

    def test_should_return_entity_form_model_based_on_entity_type(self):
        dbm = DatabaseManagerStub()
        dbm.view.registration_form_model_by_entity_type.return_value = [{'doc': {'is_registration_form': True}}]
        form_model = get_form_model_by_entity_type(dbm, ['entity_type'])
        self.assertIsInstance(form_model, EntityFormModel)
        self.assertTrue(hasattr(form_model, 'entity_type'))


class DatabaseManagerStub(DatabaseManager):
    def __init__(self):
        self.view = Mock()

    def _load_document(self, id, document_class=None):
        return Mock(FormModelDocument)
