from mangrove.forms.validators import TextLengthValidator
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

    def test_read_form_to_couch(self):
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
        form1 = Form()
        form1.save(self.manager)
        Form = forms.form_by_code(self.manager, "reg")
        form2 = Form()
        self.assertEqual(form1.uuid, form2.uuid)
        self.assertEqual(form1.name, form2.name)
        self.assertEqual(form1.code, form2.code)
        self.assertEqual(form1.state, form2.state)
        self.assertEqual(len(form1.fields), len(form2.fields))
        self.assertEqual(len(form1.fields['name'].validators), len(form2.fields['name'].validators))
        self.assertTrue(isinstance(form2.fields['name'].validators[0], TextLengthValidator))

