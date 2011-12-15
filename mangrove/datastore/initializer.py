# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore.entity_type import define_type
from mangrove.datastore.views import  sync_views
from mangrove.errors.MangroveException import EntityTypeAlreadyDefined
from mangrove.transport.reporter import REPORTER_ENTITY_TYPE


def create_entity_types(manager, entity_types):
    for entity_type in entity_types:
        try:
            define_type(manager, entity_type)
        except EntityTypeAlreadyDefined:
            pass


def run(manager):
    sync_views(manager)
    create_entity_types(manager, [REPORTER_ENTITY_TYPE])
