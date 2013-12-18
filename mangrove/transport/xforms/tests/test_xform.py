import unittest
from mock import patch, Mock
from unittest.case import SkipTest
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.form_model.field import Field, SelectField
from mangrove.transport.xforms.tests.form_content import expected_response_for_get_all_forms, expected_xform_for_project_on_reporter, expected_xform_for_project_on_subject, expected_xform_with_escaped_characters
from mangrove.transport.xforms.xform import list_all_forms, xform_for
from lxml.doctestcompare import LXMLOutputChecker

class TestXform(unittest.TestCase):
    def setUp(self):
        self.checker = LXMLOutputChecker()

    def test_should_return_list_of_required_forms(self):
        form_tuples = [("name", "id"), ("name2", "id2")]
        base_url = "baseURL"
        self.assertEqual(list_all_forms(form_tuples, base_url),
            unicode(expected_response_for_get_all_forms))

    def mock_constraint(self):
        mock_constraint = Mock()
        mock_constraint.xform_constraint.return_value = 'constraint'
        return mock_constraint

    def test_should_return_specific_form_for_project_on_reporter(self):
        dbm = Mock()
        questionnaire_mock = Mock()
        field1 = Field(ddtype=Mock(), type='text', name='name', code='code', instruction='instruction', constraints=[
            (self.mock_constraint())])
        questionnaire_mock.name = 'name'
        questionnaire_mock.fields = [field1]
        questionnaire_mock.form_code = 'form_code'
        questionnaire_mock.id = 'id'
        questionnaire_mock.is_entity_type_reporter.return_value = True
        questionnaire_mock.activeLanguages = ["en"]
        with patch("mangrove.transport.xforms.xform.FormModel") as form_model_mock:
            form_model_mock.get.return_value = questionnaire_mock
            self.assertTrue(self.checker.check_output(xform_for(dbm, "someFormId", 'rep1'),
                unicode(expected_xform_for_project_on_reporter), 0))

    def text_field(self, code):
        return Field(ddtype=Mock(), type='text', name='name', code=code, instruction='instruction', constraints=[
            (self.mock_constraint())])

    def test_should_return_specific_form_for_project_on_subject(self):
        dbm = Mock(spec=DatabaseManager)
        questionnaire_mock = Mock()
        field1 = self.text_field(code='code')
        questionnaire_mock.name = 'name'
        questionnaire_mock.fields = [field1]
        questionnaire_mock.form_code = 'form_code'
        questionnaire_mock.id = 'id'
        questionnaire_mock.is_entity_type_reporter.return_value = False
        questionnaire_mock.activeLanguages = ["en"]
        questionnaire_mock.entity_question = self.text_field(code='entity_question_code')
        entity1 = Entity(dbm, short_code="shortCode1", entity_type="someType")
        entity1._doc.data['name'] = {'value': 'nameOfEntity'}
        entities = [entity1, entity1]
        with patch("mangrove.transport.xforms.xform.FormModel") as form_model_mock:
            with patch("mangrove.transport.xforms.xform.get_all_entities") as get_all_entities_mock:
                get_all_entities_mock.return_value = entities
                form_model_mock.get.return_value = questionnaire_mock
                self.assertTrue(self.checker.check_output(xform_for(dbm, "someFormId", 'rep1'),
                    unicode(expected_xform_for_project_on_subject), 0))


    def test_should_escape_special_characters_from_requested_form(self):
        dbm = Mock()
        questionnaire_mock = Mock()
        field1 = SelectField(name='name&', code='selectcode', label="", instruction='instruction&',
            options=[{'text':'option1&'}], ddtype=Mock())
        questionnaire_mock.name = '<mock_name'
        questionnaire_mock.fields = [field1]
        questionnaire_mock.form_code = 'form_code'
        questionnaire_mock.id = 'id'
        questionnaire_mock.is_entity_type_reporter.return_value = True
        with patch("mangrove.transport.xforms.xform.FormModel") as form_model_mock:
            form_model_mock.get.return_value = questionnaire_mock
            one_of_unicode_unknown_ = xform_for(dbm, "someFormId", 'rep1')
            u = unicode(expected_xform_with_escaped_characters)
            self.assertTrue(self.checker.check_output(one_of_unicode_unknown_,
                u, 0))