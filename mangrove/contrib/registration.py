from mangrove.form_model.validators import MandatoryValidator, MobileNumberMandatoryForReporterRegistrationValidator
from mangrove.datastore.datadict import get_or_create_data_dict
from mangrove.form_model.field import HierarchyField, TextField, TelephoneNumberField, GeoCodeField
from mangrove.form_model.form_model import ENTITY_TYPE_FIELD_NAME, ENTITY_TYPE_FIELD_CODE, NAME_FIELD, NAME_FIELD_CODE, SHORT_CODE, SHORT_CODE_FIELD, LOCATION_TYPE_FIELD_NAME, LOCATION_TYPE_FIELD_CODE, MOBILE_NUMBER_FIELD, MOBILE_NUMBER_FIELD_CODE, DESCRIPTION_FIELD_CODE, GEO_CODE_FIELD, FormModel, GEO_CODE, DESCRIPTION_FIELD, REGISTRATION_FORM_CODE
from mangrove.form_model.validation import TextLengthConstraint, RegexConstraint

def create_default_reg_form_model(manager):
    form_model = _construct_registration_form(manager)
    form_model.save()
    return form_model


def _create_constraints_for_mobile_number():
    #constraints on questionnaire
    mobile_number_length = TextLengthConstraint(max=15)
    mobile_number_pattern = RegexConstraint(reg='^[0-9]+$')
    mobile_constraints = [mobile_number_length, mobile_number_pattern]
    return mobile_constraints


def _construct_registration_form(manager):
    location_type = get_or_create_data_dict(manager, name='Location Type', slug='location', primitive_type='string')
    geo_code_type = get_or_create_data_dict(manager, name='GeoCode Type', slug='geo_code', primitive_type='geocode')
    description_type = get_or_create_data_dict(manager, name='description Type', slug='description',
                                               primitive_type='string')
    mobile_number_type = get_or_create_data_dict(manager, name='Mobile Number Type', slug='mobile_number',
                                                 primitive_type='string')
    name_type = get_or_create_data_dict(manager, name='Name', slug='name', primitive_type='string')
    entity_id_type = get_or_create_data_dict(manager, name='Entity Id Type', slug='entity_id', primitive_type='string')

    question1 = HierarchyField(name=ENTITY_TYPE_FIELD_NAME, code=ENTITY_TYPE_FIELD_CODE,
                               label="What is associated subject type?",
                               language="en", ddtype=entity_id_type, instruction="Enter a type for the subject")

    question2 = TextField(name=NAME_FIELD, code=NAME_FIELD_CODE, label="What is the subject's name?",
                          defaultValue="some default value", language="en", ddtype=name_type,
                          instruction="Enter a subject name")
    question3 = TextField(name=SHORT_CODE_FIELD, code=SHORT_CODE, label="What is the subject's Unique ID Number",
                          defaultValue="some default value", language="en", ddtype=name_type,
                          instruction="Enter a id, or allow us to generate it",
                          entity_question_flag=True, constraints=[TextLengthConstraint(max=12)], required=False)
    question4 = HierarchyField(name=LOCATION_TYPE_FIELD_NAME, code=LOCATION_TYPE_FIELD_CODE,
                               label="What is the subject's location?",
                               language="en", ddtype=location_type, instruction="Enter a region, district, or commune", required=False)
    question5 = GeoCodeField(name=GEO_CODE_FIELD, code=GEO_CODE, label="What is the subject's GPS co-ordinates?",
                             language="en", ddtype=geo_code_type, instruction="Enter lat and long. Eg 20.6, 47.3", required=False)
    question6 = TextField(name=DESCRIPTION_FIELD, code=DESCRIPTION_FIELD_CODE, label="Describe the subject",
                          defaultValue="some default value", language="en", ddtype=description_type,
                          instruction="Describe your subject in more details (optional)", required=False)
    question7 = TelephoneNumberField(name=MOBILE_NUMBER_FIELD, code=MOBILE_NUMBER_FIELD_CODE,
                                     label="What is the mobile number associated with the subject?",
                                     defaultValue="some default value", language="en", ddtype=mobile_number_type,
                                     instruction="Enter the subject's number", constraints=(
            _create_constraints_for_mobile_number()), required=False)
    form_model = FormModel(manager, name="reg", form_code=REGISTRATION_FORM_CODE, fields=[
        question1, question2, question3, question4, question5, question6, question7], is_registration_model=True, entity_type=["Registration"],
        validators=[MandatoryValidator(), MobileNumberMandatoryForReporterRegistrationValidator()])
    return form_model