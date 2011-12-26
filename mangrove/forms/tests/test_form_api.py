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
            'fields': [{
                '_class': "TextField",
                'name': "name",
                "code": "na",
                "label": "What is the name?",
                "default":"",
            }]
        }
        form = forms.Form.build_from_dct(dct)
        self.assertEqual(1, len(form().fields))
        self.assertEqual("reg", form().code)

    def test_get_hold_of_field_from_form(self):
        dct = {
            'code': "reg",
            'fields': [{
                '_class': "TextField",
                'name': "name",
                "code": "na",
                "label": "What is the name?",
                "default":"",
                "required":True
            }]
        }
        form = forms.Form.build_from_dct(dct)
        self.assertEqual("na", form()['name'].code)
        self.assertTrue(form()['name'].required)

    def test_validate_submission_with_no_constraints_added(self):
        dct = {
            'code': "reg",
            'fields': [{
                '_class': "TextField",
                'name': "name",
                "code": "na",
                "label": "What is the name?",
                "default":"",
                "required":True
            }]
        }
        form = forms.Form.build_from_dct(dct)
        self.assertFalse(form(data={}).is_valid())

    def test_validate_submission_with_length_constraint_added(self):
        dct = {
            'code': "reg",
            'fields': [{
                '_class': "TextField",
                'name': "name",
                "code": "na",
                "label": "What is the name?",
                "default":"",
                "required":True,
                "validators":[
                    {'_class':'TextLengthValidator',
                     'min':2,
                     'max':5}
                ]
            }]
        }
        form = forms.Form.build_from_dct(dct)
        self.assertTrue(form(data={'name':'foo'}).is_valid())
        self.assertFalse(form(data={'name':'foobar'}).is_valid())

    def test_should_add_multiple_validators(self):
        dct = {
            'code': "reg",
            'fields': [{
                '_class': "TextField",
                'name': "name",
                "code": "na",
                "label": "What is the name?",
                "default": "",
                "required": True,
                "validators": [
                        {'_class': 'TextLengthValidator',
                         'min': 2,
                         'max': 5},
                        {'_class': 'RegexValidator',
                         'pattern': "^[A-Za-z0-9]+$"}
                ]
            }]
        }
        Form = forms.Form.build_from_dct(dct)
        form = Form()
        self.assertEqual(2,len(form.fields['name'].validators))
        self.assertTrue(Form(data={'name':'foo'}).is_valid())
        self.assertFalse(Form(data={'name':'foo.'}).is_valid())

    def test_should_have_cleaned_data_after_validation(self):
        dct = {
            'code': "reg",
            'fields': [{
                '_class': "TextField",
                'name': "name",
                "code": "na",
                "label": "What is the name?",
                "default": "",
                "required": True,
                "validators": [
                        {'_class': 'TextLengthValidator',
                         'min': 2,
                         'max': 5},
                        {'_class': 'RegexValidator',
                         'pattern': "^[A-Za-z0-9]+$"}
                ]
            }]
        }
        Form = forms.Form.build_from_dct(dct)
        form = Form(data={'name':'foo'})
        self.assertTrue(form.is_valid())
        self.assertEqual({'name':'foo'}, form.cleaned_data)

    def test_should_not_have_cleaned_data_after_incorrect_validation(self):
        dct = {
            'code': "reg",
            'fields': [{
                '_class': "TextField",
                'name': "name",
                "code": "na",
                "label": "What is the name?",
                "default": "",
                "required": True,
                "validators": [
                        {'_class': 'TextLengthValidator',
                         'min': 2,
                         'max': 5},
                        {'_class': 'RegexValidator',
                         'pattern': "^[A-Za-z0-9]+$"}
                ]
            }]
        }
        Form = forms.Form.build_from_dct(dct)
        form = Form(data={'name':'foo.'})
        self.assertFalse(form.is_valid())
        with self.assertRaises(AttributeError):
            foo = form.cleaned_data

    def test_should_create_meta_class_from_metadata(self):
        dct = {
            'code': "reg",
            'fields': [{
                '_class': "TextField",
                'name': "name",
                "code": "na",
                "label": "What is the name?",
                "default":"",
                "required":True
            }],
            "metadata":{
                "registration": True,
                "entity_type": "reporter"
            }
        }
        Form = forms.Form.build_from_dct(dct)
        self.assertEqual("reporter", Form.Meta.entity_type)
