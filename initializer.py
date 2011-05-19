# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datastore import initializer as datastore_initializer
from form_model import initializer as form_model_initializer


def run(manager):
    datastore_initializer.run(manager)
    form_model_initializer.run(manager)
