import uuid
from mangrove.bootstrap import initializer
from mangrove.contrib.deletion import ENTITY_DELETION_FORM_CODE, create_default_delete_form_model
from mangrove.contrib.registration import create_default_reg_form_model, GLOBAL_REGISTRATION_FORM_CODE
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.entity import get_by_short_code, Entity
from mangrove.datastore.entity_type import define_type
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, EntityTypeAlreadyDefined, NumberNotRegisteredException, DataObjectNotFound
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.transport.repository.reporters import find_reporters_by_from_number


def create_dbmanager_for_ut(cls):
        cls.db_name = 'mangrove-test-unit'
        cls.manager = get_db_manager('http://localhost:5984/', cls.db_name)
        _delete_db_and_remove_db_manager(cls.manager)
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

def uniq(prefix):
    return prefix + "-" + str(uuid.uuid1())

def ut_reporter_id():
    return uniq("utrep")

def safe_delete_reporter_by_phone(manager, mobile_number):
    try :
        users = find_reporters_by_from_number(manager, mobile_number)
        for user in users:
            user.delete()
    except NumberNotRegisteredException:
        pass

def delete_and_create_entity_instance(manager, ENTITY_TYPE, location, short_code):
    try:
        entity = get_by_short_code(dbm=manager, short_code=short_code,entity_type=ENTITY_TYPE)
        entity.delete()
    except DataObjectNotFound:
        pass

    e = Entity(manager, entity_type=ENTITY_TYPE, location=location, short_code=short_code)
    id1 = e.save()
    return e, id1