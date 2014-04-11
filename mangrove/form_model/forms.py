from mangrove.errors.MangroveException import MangroveException

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

        self.survey_response = survey_response
        self.survey_response.set_form(form_model)
        self.survey_response.set_answers(form_answers)

    @property
    def unique_id_question_code(self):
        return self.form_model.entity_questions[0].code if self.form_model.entity_questions else None

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
            self.survey_response.update(self.form_model, self.data())
            #self.entity.update_latest_data(data=self.data())
        except MangroveException as exception:
            self.survey_response.set_status(self.errors)
            self.errors = exception.message
            raise

        self.saved = True
        return self.survey_response

    def data(self):
        return [(self.form_model.get_field_by_code(code).name, value)
                for (code, value) in
                (self._cleaned_data.items())]


