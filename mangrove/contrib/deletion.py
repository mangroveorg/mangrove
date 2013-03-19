# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.contrib.delete_validators import EntityShouldExistValidator
from mangrove.form_model.validators import MandatoryValidator
from mangrove.datastore.datadict import get_or_create_data_dict
from mangrove.form_model.field import HierarchyField, TextField
from mangrove.form_model.form_model import ENTITY_TYPE_FIELD_NAME, ENTITY_TYPE_FIELD_CODE, SHORT_CODE, SHORT_CODE_FIELD, FormModel
from mangrove.form_model.validation import TextLengthConstraint

ENTITY_DELETION_FORM_CODE = "delete"

def create_default_delete_form_model(manager):
    form_model = _construct_global_deletion_form(manager)
    form_model.save()
    return form_model


def _construct_global_deletion_form(manager):
    entity_id_dd = get_or_create_data_dict(manager, name='Entity Id', slug='entity_id', primitive_type='string')
    entity_type_dd = get_or_create_data_dict(manager, name='Entity Type', slug='entity_type', primitive_type='string')

    question1 = HierarchyField(name=ENTITY_TYPE_FIELD_NAME, code=ENTITY_TYPE_FIELD_CODE,
        label="What is the entity type",
        ddtype=entity_type_dd, instruction="Enter a type for the entity")

    question2 = TextField(name=SHORT_CODE_FIELD, code=SHORT_CODE, label="What is the entity's Unique ID Number",
        defaultValue="some default value", ddtype=entity_id_dd,
        instruction="Enter the id of the entity you want to delete",
        entity_question_flag=True, constraints=[])

    form_model = FormModel(manager, name=ENTITY_DELETION_FORM_CODE, form_code=ENTITY_DELETION_FORM_CODE, fields=[
        question1, question2], entity_type=["deletion"],
        validators=[MandatoryValidator(), EntityShouldExistValidator()])
    return form_model