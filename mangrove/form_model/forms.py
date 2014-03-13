from mangrove.errors.MangroveException import MangroveException
from mangrove.datastore.entity import get_by_short_code

class EditSurveyResponseForm(object):

    def __init__(self, dbm, survey_response, form_model, form_answers):
        assert dbm is not None
        assert survey_response is not None
        assert form_model is not None

        self.saved = False

        self.dbm = dbm
        self.form_model = form_model
        self.form_model.bind(form_answers)
        self._cleaned_data, self.errors = form_model.validate_submission(values=form_answers)
        self.is_valid = (self.errors is None or len(self.errors) == 0)

        self.entity_type = form_model.entity_type
        entity_short_code = self.get_answer_for(self.unique_id_question_code)
        self.short_code = entity_short_code.lower() if entity_short_code is not None else None
        self.entity = get_by_short_code(dbm=dbm, short_code=self.short_code, entity_type=self.entity_type)

        self.survey_response = survey_response
        self.survey_response.set_form(form_model)
        self.survey_response.set_answers(self.short_code, form_answers)

    @property
    def unique_id_question_code(self):
        return self.form_model.unique_id_field.code

    @property
    def data_record_id(self):
        return self.survey_response.data_record_id if self.survey_response is not None else None

    @property
    def is_registration(self):
        return self.form_model.is_entity_registration_form()

    def save(self):
        assert self.is_valid
        try:
            self.survey_response.set_status(self.errors)
            self.survey_response.update(self.form_model, self.data(), self.entity)
            #self.entity.update_latest_data(data=self.data())
        except MangroveException as exception:
            self.survey_response.set_status(self.errors)
            self.errors = exception.message
            raise

        self.saved = True
        return self.survey_response

    def get_answer_for(self, code):
        for key in self._cleaned_data:
            if key.lower() == code.lower():
                return self._cleaned_data[key]
        return None

    def data(self):
        return [(self.form_model._get_field_by_code(code).name, value)
                for (code, value) in
                (self._cleaned_data.items())]


