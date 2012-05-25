import unittest
from mock import patch, Mock
from selenium.webdriver.remote.utils import return_value_if_exists
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.form_model.field import Field
from mangrove.transport.xforms.tests.form_content import expected_response_for_get_all_forms, expected_xform_for_project_on_reporter, expected_xform_for_project_on_subject
from mangrove.transport.xforms.xform import list_all_forms, xform_for
from lxml.doctestcompare import LXMLOutputChecker

class TestXform(unittest.TestCase):
    def setUp(self):
        self.checker = LXMLOutputChecker()

    def test_should_return_list_of_required_forms(self):
        form_tuples = [("name", "id"), ("name2", "id2")]
        base_url = "baseURL"
        self.assertTrue(self.checker.check_output(list_all_forms(form_tuples, base_url),
            unicode(expected_response_for_get_all_forms), 0))


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
        questionnaire_mock.entity_defaults_to_reporter.return_value = True
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
        questionnaire_mock.entity_defaults_to_reporter.return_value = False
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


