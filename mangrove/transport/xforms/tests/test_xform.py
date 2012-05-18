import unittest
from mock import patch, Mock
from selenium.webdriver.remote.utils import return_value_if_exists
from mangrove.form_model.field import Field
from mangrove.transport.xforms.tests.form_content import expected_response_for_get_all_forms, expected_response_for_get_specific_form
from mangrove.transport.xforms.xform import list_all_forms, xform_for
from lxml.doctestcompare import LXMLOutputChecker

class TestXform(unittest.TestCase):

    def setUp(self):
        self.checker = LXMLOutputChecker()

    def test_should_return_list_of_required_forms(self):
        form_tuples = [("name", "id"), ("name2", "id2")]
        base_url = "baseURL"
        self.assertTrue(self.checker.check_output(list_all_forms(form_tuples, base_url), unicode(expected_response_for_get_all_forms), 0))


    def mock_constraint(self):
        mock_constraint = Mock()
        mock_constraint.xform_constraint.return_value = 'constraint'
        return mock_constraint

    def test_should_return_specific_form(self):
        dbm = Mock()
        questionnaire_mock = Mock()
        field1 = Field(ddtype=Mock(), type='text', name='name', code='code', instruction='instruction',constraints=[
            (self.mock_constraint())])
        questionnaire_mock.name = 'name'
        questionnaire_mock.fields = [field1]
        questionnaire_mock.form_code = 'form_code'
        with patch("mangrove.transport.xforms.xform.FormModel") as form_model_mock:
            form_model_mock.get.return_value = questionnaire_mock
            self.assertTrue(self.checker.check_output(xform_for(dbm, "someFormId", 'rep1'), unicode(expected_response_for_get_specific_form), 0))


