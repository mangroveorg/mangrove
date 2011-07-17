# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.errors.MangroveException import DataObjectNotFound, FormModelDoesNotExistsException
from mangrove.form_model.form_model import create_default_reg_form_model, get_form_model_by_code, \
    REGISTRATION_FORM_CODE


def _delete_reg_form_if_exists(manager):
    try:
        form_model = get_form_model_by_code(manager, REGISTRATION_FORM_CODE)
        form_model.delete()
    except FormModelDoesNotExistsException:
        pass


def _update_reg_form(manager):
    _delete_reg_form_if_exists(manager)
    create_default_reg_form_model(manager)


def run(manager):
    _update_reg_form(manager)
