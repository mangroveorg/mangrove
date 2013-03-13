from copy import copy
from mangrove.errors import MangroveException
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, InactiveFormModelException
from mangrove.form_model.form_model import get_form_model_by_code, DataFormSubmission
from mangrove.transport.player.parser import WebParser
from mangrove.transport.submissions import Submission
from mangrove.transport import Response

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
        form_model = get_form_model_by_code(self.dbm, form_code)
        submission.update_form_model_revision(form_model.revision)

        if form_model.is_inactive():
            raise InactiveFormModelException(form_model.form_code)

        try:
            form_model.bind(values)
            cleaned_data, errors = form_model.validate_submission(values=values)
            form_submission = self.save(form_model, cleaned_data, errors)

            submission.values[form_model.entity_question.code] = form_submission.short_code
            submission.update(form_submission.saved, form_submission.errors, form_submission.data_record_id,
                form_model.is_in_test_mode())
            self.log_request(form_submission.saved, transport_info.source, message)

            return Response(reporter_names, submission.uuid, form_submission.saved, form_submission.errors,
                form_submission.data_record_id,
                form_submission.short_code, form_submission.cleaned_data, form_submission.is_registration,
                form_submission.entity_type,
                form_submission.form_model.form_code)

        except (MangroveException, FormModelDoesNotExistsException) as exception:
            submission.update(status=False, errors=exception.message, is_test_mode=form_model.is_in_test_mode())
            raise

    def log_request(self, status, source, message):
        if self.logger is not None:
            log_entry = "message: " + str(message) + "|source: " + source + "|"
            log_entry += "status: True" if status else "status: False"
            self.logger.info(log_entry)


#    def save_survey_response(self, request):
#        self.parser = SurveyResponseService.PARSERS.get(request.transport.transport)
#        assert request is not None
#        form_code, values = self.parser.parse(request.message)
#
#        submission = self._create_submission_log(request.transport, form_code, copy(values))
#        form_model = get_form_model_by_code(self.dbm, form_code)
#        submission.update_form_model_revision(form_model.revision)
#
#        if form_model.is_inactive():
#            raise InactiveFormModelException(form_model.form_code)
#
#        try:
#            form_model.bind(values)
#            cleaned_data, errors = form_model.validate_submission(values=values)
#            form_submission = self.save(form_model, cleaned_data, errors)
#
#            submission.values[form_model.entity_question.code] = form_submission.short_code
#            submission.update(form_submission.saved, form_submission.errors, form_submission.data_record_id,
#                form_model.is_in_test_mode())
#
#            self.log_request(form_submission, request)
#
#            return Response([], submission.uuid, form_submission.saved, form_submission.errors,
#                form_submission.data_record_id,
#                form_submission.short_code, form_submission.cleaned_data, form_submission.is_registration,
#                form_submission.entity_type,
#                form_submission.form_model.form_code)
#        except (MangroveException, FormModelDoesNotExistsException) as exception:
#            submission.update(status=False, errors=exception.message, is_test_mode=form_model.is_in_test_mode())
#            raise
#
#

    def save(self, form_model, cleaned_data, errors):
        form_submission = DataFormSubmission(form_model, cleaned_data, errors)
        if form_submission.is_valid:
            form_submission.save(self.dbm)
        return form_submission

    def edit_survey_response(self):
        pass

    def delete_survey_response(self):
        pass
