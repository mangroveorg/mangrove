from mangrove.forms import forms
from mangrove.forms.fields import TextField, GeoCodeField, TelephoneNumberField, HierarchyField
from mangrove.forms.validators import TextLengthValidator, RegexValidator

#TODO Introduce an exception in the meta class to indicate user has not specified a code
#TODO Raise Exception in MC if two fields have same code
class RegistrationForm(forms.Form):
    t = HierarchyField(code="t", label="What is associated subject type?", instruction="Enter a type for the subject",
                                 required=True)
    n = TextField(code="n", label="What is the subject's name?", instruction="Enter a subject name", required=True)
    s = TextField(code="s", label="What is the subject's Unique ID Number",
                          instruction="Enter a id, or allow us to generate it",validators=[TextLengthValidator(max=12)])
    l = HierarchyField(code="l",
                               label="What is the subject's location?", instruction="Enter a region, district, or commune")
    g = GeoCodeField(code="g", label="What is the subject's GPS co-ordinates?", instruction="Enter lat and long. Eg 20.6, 47.3")
    d = TextField(code="d", label="Describe the subject", instruction="Describe your subject in more details (optional)")
    m = TelephoneNumberField(code="m",
                                     label="What is the mobile number associated with the subject?",
                                     instruction="Enter the subject's number", validators=(
            [TextLengthValidator(max=15), RegexValidator('^[0-9]+$')]), )
    code = 'reg'

    class Meta:
        entity_question_field = "short_code"
        registration = True
        state = "Active"


def create_default_registration_form(manager):
    registration_form = RegistrationForm()
    registration_form.save(manager)
    return registration_form
