# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from views import view_js
from mangrove.contrib.registration import create_default_reg_form_model
from mangrove.datastore.entity_type import define_type
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, EntityTypeAlreadyDefined
from mangrove.form_model.form_model import get_form_model_by_code, REGISTRATION_FORM_CODE
from mangrove.transport.reporter import REPORTER_ENTITY_TYPE


def run(manager):
    sync_views(manager)
    _create_entity_types(manager, [REPORTER_ENTITY_TYPE])
    _delete_reg_form_if_exists(manager)
    create_default_reg_form_model(manager)


def _delete_reg_form_if_exists(manager):
    try:
        form_model = get_form_model_by_code(manager, REGISTRATION_FORM_CODE)
        form_model.delete()
    except FormModelDoesNotExistsException:
        pass


def _create_entity_types(manager, entity_types):
    for entity_type in entity_types:
        try:
            define_type(manager, entity_type)
        except EntityTypeAlreadyDefined:
            pass

def _create_views(dbm):
    """Creates a standard set of views in the database"""
    database_manager = dbm
    for v in view_js.keys():
        if not _exists_view(v, database_manager):
            funcs = view_js[v]
            map = (funcs['map'] if 'map' in funcs else None)
            reduce = (funcs['reduce'] if 'reduce' in funcs else None)
            database_manager.create_view(v, map, reduce)


def sync_views(dbm):
    """Updates or Creates a standard set of views in the database"""
    database_manager = dbm
    for v in view_js.keys():
        funcs = view_js[v]
        map = (funcs['map'] if 'map' in funcs else None)
        reduce = (funcs['reduce'] if 'reduce' in funcs else None)
        database_manager.create_view(v, map, reduce)


def _exists_view(aggregation, database_manager):
    entity_type_views = database_manager._load_document('_design/%s' % aggregation)
    if entity_type_views is not None and entity_type_views['views'].get(aggregation):
        return True
    return False


