import unittest
from mock import patch, Mock
from mangrove.transport.xforms.tests.form_content import expected_response_for_get_all_forms, expected_response_for_get_specific_form
from mangrove.transport.xforms.xform import list_all_forms, xform_for

class TestXform(unittest.TestCase):
    def test_should_return_list_of_required_forms(self):
        form_tuples = [("name", "id"), ("name2", "id2")]
        base_url = "baseURL"
        self.assertEquals(list_all_forms(form_tuples, base_url), unicode(expected_response_for_get_all_forms))

    def test_should_return_specific_form(self):
        dbm = Mock()
        questionnaire_mock = Mock()
        field1 = Mock()
        field1.type = 'type'
        field1.name = 'name'
        field1.code = 'code'
        field1.instruction = 'instruction'
        questionnaire_mock.name = 'name'
        questionnaire_mock.fields = [field1]
        questionnaire_mock.form_code = 'form_code'
        with patch("mangrove.transport.xforms.xform.FormModel") as form_model_mock:
            form_model_mock.get.return_value = questionnaire_mock
            self.assertEquals(xform_for(dbm, "someFormId"), unicode(expected_response_for_get_specific_form))


