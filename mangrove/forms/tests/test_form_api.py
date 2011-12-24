import unittest
from mangrove.forms.fields import TextField
from mangrove.forms import forms

class TestFormAPI(unittest.TestCase):

    def test_create_new_form(self):
        class FooForm(forms.Form):
            name = TextField("foo", "f", "What is foo?")

        form = FooForm()
        self.assertEqual(2, len(form.fields))




