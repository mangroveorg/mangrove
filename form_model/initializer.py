# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore.datadict import get_or_create_data_dict
from mangrove.form_model.field import TextField
from mangrove.form_model.form_model import RegistrationFormModel

def run(manager):
    create_default_reg_form_model(manager)


def create_default_reg_form_model(manager):
    location_type = get_or_create_data_dict(manager, name='Location Type', slug='location', primitive_type='string')
    description_type = get_or_create_data_dict(manager, name='description Type', slug='description', primitive_type='string')
    mobile_number_type = get_or_create_data_dict(manager, name='Mobile Number Type', slug='mobile_number', primitive_type='string')
    name_type = get_or_create_data_dict(manager, name='Name', slug='Name', primitive_type='string')
    entity_id_type = get_or_create_data_dict(manager, name='Entity Id Type', slug='entity_id', primitive_type='string')

    #Create registration questionnaire
    question1 = TextField(name="entity_type", question_code="T", label="What is associated entity type?",
                          language="eng", entity_question_flag=False, ddtype=entity_id_type)

    question2 = TextField(name="name", question_code="N", label="What is the entity's name?",
                          defaultValue="some default value", language="eng", ddtype=name_type)
    question3 = TextField(name="short_name", question_code="S", label="What is the entity's short name?",
                          defaultValue="some default value", language="eng", ddtype=name_type)
    question4 = TextField(name="location", question_code="L", label="What is the entity's location?",
                          defaultValue="some default value", language="eng", ddtype=location_type)
    question5 = TextField(name="description", question_code="D", label="Describe the entity",
                          defaultValue="some default value", language="eng", ddtype=description_type)
    question6 = TextField(name="mobile_number", question_code="M", label="What is the associated mobile number?",
                          defaultValue="some default value", language="eng", ddtype=mobile_number_type)
    form_model = RegistrationFormModel(manager, name="REG", form_code="REG", fields=[
                    question1, question2, question3, question4, question5, question6])
    form_model.save()
