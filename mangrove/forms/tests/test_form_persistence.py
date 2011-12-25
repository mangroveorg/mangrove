from mangrove.forms import forms
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestFormPersistence(MangroveTestCase):

    def setUp(self):
        MangroveTestCase.setUp(self)

    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def test_save_form_to_couch(self):
        dct = {
            'code': "reg",
            'name': "random_registration_form",
            'state': 'Test',
            'fields': [{
                '_class': "TextField",
                'name': "name",
                "code": "na",
                "label": "What is the name?",
                "default": "",
                "required": True,
                "validators": [
                        {
                        '_class': 'TextLengthValidator',
                        'min': 2,
                        'max': 5
                    }
                ]
            }],
            'metadata': {
                'is_registration': True,
                'entity_type': 'Clinic'
            }
        }
        Form = forms.Form.build_from_dct(dct)
        form = Form()
        form.save(self.manager)
        self.assertTrue(form.uuid)
