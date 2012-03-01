import unittest
from mangrove.forms.fields import TextField
from mangrove.forms import forms

class TestFormAPI(unittest.TestCase):

    def test_create_new_form(self):
        class FooForm(forms.Form):
            code = "bar"
            name = TextField("foo", "f", "What is foo?")

            class Meta:
                registration = True
                entity_type = "Clinic"

        form = FooForm()
        self.assertEqual(1, len(form.fields))
        self.assertEqual("bar", form.code)
        self.assertTrue(form.registration())


    def test_create_new_form_from_dct(self):
        dct = {
            'code': "reg",
            'fields': {
                'name':
                        {
                            '_class': "TextField",
                            "code": "na",
                            "label": "What is the name?",
                            "default": "",
                            "creation_counter": 0
                        }
            }
        }
        form = forms.Form.build_from_dct(dct)
        self.assertEqual(1, len(form().fields))
        self.assertEqual("reg", form().code)

    def test_get_hold_of_field_from_form(self):
        dct = {
            'code': "reg",
            'fields': {'name': {
                '_class': "TextField",
                "code": "na",
                "label": "What is the name?",
                "default":"",
                "required":True,
                "creation_counter":0
            }}
        }
        form = forms.Form.build_from_dct(dct)
        self.assertEqual("na", form()['name'].code)
        self.assertTrue(form()['name'].required)

    def test_validate_submission_with_no_constraints_added(self):
        dct = {
            'code': "reg",
            'fields': {"name": {
                '_class': "TextField",
                "code": "na",
                "label": "What is the name?",
                "default":"",
                "required":True,
                "creation_counter":0
            }}
        }
        form = forms.Form.build_from_dct(dct)
        self.assertFalse(form(data={}).validate_submission())

    def test_validate_submission_with_length_constraint_added(self):
        dct = {
            'code': "reg",
            'fields': {
                "name": {
                '_class': "TextField",
                "code": "na",
                "label": "What is the name?",
                "default":"",
                "required":True,
                "creation_counter":0,
                "validators":[
                    {'_class':'TextLengthValidator',
                     'min':2,
                     'max':5}
                ]
                }
            }
        }
        form = forms.Form.build_from_dct(dct)
        self.assertTrue(form(data={'name':'foo'}).validate_submission())
        self.assertFalse(form(data={'name':'foobar'}).validate_submission())

    def test_should_add_multiple_validators(self):
        dct = {
            'code': "reg",
            'fields': {'name': {
                '_class': "TextField",
                "code": "na",
                "label": "What is the name?",
                "default": "",
                "required": True,
                "creation_counter":0,
                "validators": [
                        {'_class': 'TextLengthValidator',
                         'min': 2,
                         'max': 5},
                        {'_class': 'RegexValidator',
                         'pattern': "^[A-Za-z0-9]+$"}
                ]
            }}
        }
        Form = forms.Form.build_from_dct(dct)
        form = Form()
        self.assertEqual(2,len(form.fields['name'].validators))
        self.assertTrue(Form(data={'name':'foo'}).validate_submission())
        self.assertFalse(Form(data={'name':'foo.'}).validate_submission())

    def test_should_have_cleaned_data_after_validation(self):
        dct = {
            'code': "reg",
            'fields': {"name": {
                '_class': "TextField",
                "code": "na",
                "label": "What is the name?",
                "default": "",
                "required": True,
                "creation_counter":0,
                "validators": [
                        {'_class': 'TextLengthValidator',
                         'min': 2,
                         'max': 5},
                        {'_class': 'RegexValidator',
                         'pattern': "^[A-Za-z0-9]+$"}
                ]
            }}
        }
        Form = forms.Form.build_from_dct(dct)
        form = Form(data={'name':'foo'})
        self.assertTrue(form.validate_submission())
        self.assertEqual({'name':'foo'}, form.cleaned_data)

    def test_should_not_have_cleaned_data_after_incorrect_validation(self):
        dct = {
            'code': "reg",
            'fields': {"name": {
                '_class': "TextField",
                "code": "na",
                "label": "What is the name?",
                "default": "",
                "required": True,
                "creation_counter":0,
                "validators": [
                        {'_class': 'TextLengthValidator',
                         'min': 2,
                         'max': 5},
                        {'_class': 'RegexValidator',
                         'pattern': "^[A-Za-z0-9]+$"}
                ]
            }}
        }
        Form = forms.Form.build_from_dct(dct)
        form = Form(data={'name':'foo.'})
        self.assertFalse(form.validate_submission())
        with self.assertRaises(AttributeError):
            foo = form.cleaned_data

    def test_should_create_meta_class_from_metadata(self):
        dct = {
            'code': "reg",
            'fields': {"name":{
                '_class': "TextField",
                "code": "na",
                "label": "What is the name?",
                "creation_counter":0,
                "default":"",
                "required":True
            }},
            "metadata":{
                "registration": False,
                "entity_type": "reporter"
            }
        }
        Form = forms.Form.build_from_dct(dct)
        self.assertEqual("reporter", Form.Meta.entity_type)
        self.assertFalse(Form().registration())
        self.assertEqual("reporter", Form().entity_type())
