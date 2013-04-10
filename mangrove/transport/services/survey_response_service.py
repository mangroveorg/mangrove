from copy import copy
from mangrove.form_model.forms import EditSurveyResponseForm
from mangrove.form_model.form_submission import DataFormSubmission
from mangrove.errors import MangroveException
from mangrove.errors.MangroveException import InactiveFormModelException
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.transport.player.parser import WebParser
from mangrove.transport.contract.submission import Submission
from mangrove.transport.contract.response import Response
from mangrove.transport.repository.survey_responses import SurveyResponse

class SurveyResponseService(object):
    PARSERS = {'web': WebParser()}

    def __init__(self, dbm, logger=None):
        self.dbm = dbm
        self.logger = logger

    def _create_submission_log(self, transport_info, form_code, values):
        submission = Submission(self.dbm, transport_info, form_code, values=copy(values))
        submission.save()
        return submission

    def save_survey(self, form_code, values, reporter_names, transport_info, message):
        submission = self._create_submission_log(transport_info, form_code, copy(values))
        survey_response = SurveyResponse(self.dbm, transport_info, form_code, copy(values))

        form_model = get_form_model_by_code(self.dbm, form_code)
        submission.update_form_model_revision(form_model.revision)
        survey_response.set_form(form_model)

        if form_model.is_inactive():
            raise InactiveFormModelException(form_model.form_code)

        #        TODO : validate_submission should use form_model's bound values
        form_model.bind(values)
        cleaned_data, errors = form_model.validate_submission(values=values)

        form_submission = DataFormSubmission(form_model, cleaned_data, errors)
        try:
            if form_submission.is_valid:
                form_submission.save(self.dbm)
            survey_response.set_answers(form_submission.short_code, values)

            submission.update(form_submission.saved, form_submission.errors, form_model.entity_question.code,
                form_submission.short_code, form_submission.data_record_id, form_model.is_in_test_mode())
        except MangroveException as exception:
            submission.update(status=False, errors=exception.message, is_test_mode=form_model.is_in_test_mode())
            errors = exception.message
            raise
        finally:
            survey_response.set_status(errors)
            survey_response.create(form_submission.data_record_id)
            self.log_request(form_submission.saved, transport_info.source, message)

        return Response(reporter_names, submission.uuid, survey_response.uuid, form_submission.saved,
            form_submission.errors, form_submission.data_record_id, form_submission.short_code,
            form_submission.cleaned_data, form_submission.is_registration, form_submission.entity_type,
            form_submission.form_model.form_code)


    def edit_survey(self, form_code, values, reporter_names, transport_info, message, survey_response):
        submission = self._create_submission_log(transport_info, form_code, copy(values))
        form_model = get_form_model_by_code(self.dbm, form_code)
        submission.update_form_model_revision(form_model.revision)

        if form_model.is_inactive():
            raise InactiveFormModelException(form_model.form_code)

        form = EditSurveyResponseForm(self.dbm, survey_response, form_model, values)
        try:
            if form.is_valid:
                survey_response = form.save()
            submission.update(form.saved, form.errors, form.entity_question_code,
                form.short_code, form.data_record_id, form_model.is_in_test_mode())
        except MangroveException as exception:
            submission.update(status=False, errors=exception.message, is_test_mode=form_model.is_in_test_mode())
            raise
        finally:
            self.log_request(form.saved, transport_info.source, message)
        return Response(reporter_names, submission.uuid, survey_response.uuid, form.saved,
            form.errors, form.data_record_id, form.short_code,
            form._cleaned_data, form.is_registration, form.entity_type,
            form.form_model.form_code)

    def log_request(self, status, source, message):
        if self.logger is not None:
            log_entry = "message: " + str(message) + "|source: " + source + "|"
            log_entry += "status: True" if status else "status: False"
            self.logger.info(log_entry)
