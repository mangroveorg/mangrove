import uuid
from mangrove.bootstrap import initializer
from mangrove.contrib.deletion import ENTITY_DELETION_FORM_CODE, create_default_delete_form_model
from mangrove.contrib.registration import create_default_reg_form_model, GLOBAL_REGISTRATION_FORM_CODE
from mangrove.datastore.database import get_db_manager
from mangrove.datastore.entity_type import define_type
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, EntityTypeAlreadyDefined
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.transport.repository.reporters import find_reporters_by_from_number


def create_dbmanager_for_ut(cls):
        cls.db_name = 'mangrove-test-unit'
        cls.manager = get_db_manager('http://localhost:5984/', cls.db_name)
        initializer._create_views(cls.manager)

def delete_and_create_form_model(manager, form_code):
    try:
        form =get_form_model_by_code(manager, form_code)
        if form:
            form.delete()
    except FormModelDoesNotExistsException:
        pass
    if form_code == GLOBAL_REGISTRATION_FORM_CODE:
        return create_default_reg_form_model(manager)
    elif form_code == ENTITY_DELETION_FORM_CODE:
        return create_default_delete_form_model(manager)



def safe_define_type(manager,  type):
    try:
        define_type(manager, type)
    except EntityTypeAlreadyDefined:
        pass

def id(prefix):
    return prefix + "-" + str(uuid.uuid1())

def ut_reporter_id():
    return id("utrep")

def delete_reporter_by_phone(manager, mobile_number):
    users = find_reporters_by_from_number(manager, mobile_number)
    for user in users:
        user.delete()