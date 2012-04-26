import unittest
from mangrove.transport.xforms.xform import list_all_forms

class TestXform(unittest.TestCase):
    def test_should_return_list_of_required_forms(self):
        form_tuples = [("name", "id"), ("name2", "id2")]
        base_url = "baseURL"
        expected_response = """<forms>
                        <formID>name</formID>
            <form url="baseURL/id">name</form>
            <formID>name</formID>

                    <formID>name2</formID>
            <form url="baseURL/id2">name2</form>
            <formID>name2</formID>

            </forms>"""
        self.assertEquals(list_all_forms(form_tuples, base_url), unicode(expected_response))
