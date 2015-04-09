
from mangrove.errors.MangroveException import MangroveException
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.transport.player.handler import handler_factory
from mangrove.transport.work_flow import RegistrationWorkFlow


class IdentificationNumberService(object):
    def __init__(self, dbm):
        self.dbm = dbm
    def save_identification_number(self, form_code, reporter_entity_names, reporter_id, values, location_tree):
        form_model = get_form_model_by_code(self.dbm, form_code)
        return  self._submit_subject(form_model, values, reporter_entity_names, location_tree)

    def _submit_subject(self, form_model, values, reporter_names, location_tree):
        try:
            values = RegistrationWorkFlow(self.dbm, form_model, location_tree).process(values)
            form_model.bind(values)
            cleaned_data, errors = form_model.validate_submission(values=values)
            handler = handler_factory(self.dbm, form_model)
            response = handler.handle(form_model, cleaned_data, errors,  reporter_names, location_tree)
            return response
        except MangroveException:
            raise