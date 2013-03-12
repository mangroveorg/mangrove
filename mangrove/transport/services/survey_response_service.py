from copy import copy
from mangrove.errors import MangroveException
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, InactiveFormModelException
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.transport.facade import GeneralWorkFlow
from mangrove.transport.player.handler import SubmissionHandler
from mangrove.transport.player.parser import WebParser
from mangrove.transport.submissions import Submission

class SurveyResponseService(object):
    PARSERS = {'web': WebParser()}

    def __init__(self, dbm, location_tree=None):
        self.dbm = dbm
        self.location_tree = location_tree


    def _create_submission_log(self, transport, form_code, values):
        try:
            form_model = get_form_model_by_code(self.dbm, form_code)
            form_model_revision = form_model.revision
        except FormModelDoesNotExistsException:
            form_model_revision = None

        submission = Submission(self.dbm, transport, form_code, form_model_revision, copy(values))
        submission.save()
        return submission

    def save_survey_response(self, request, logger=None):
        self.parser = SurveyResponseService.PARSERS.get(request.transport)
        assert request is not None
        form_code, values = self.parser.parse(request.message)
        submission = self._create_submission_log(request.transport, form_code, copy(values))
        form_model = get_form_model_by_code(self.dbm, form_code)
        values = GeneralWorkFlow().process(values)

        try:
            if form_model.is_inactive():
                raise InactiveFormModelException(form_model.form_code)
            form_model.bind(values)
            cleaned_data, errors = form_model.validate_submission(values=values)
            response = SubmissionHandler.handle(form_model, cleaned_data, errors, submission.uuid, [],
                self.location_tree, submission)
            submission.values[form_model.entity_question.code] = response.short_code
            submission.update(response.success, response.errors, response.datarecord_id,
                form_model.is_in_test_mode())
            if logger is not None:
                log_entry = "message: " + str(request.message) + "|source: " + request.transport.source + "|"
                log_entry += "status: True" if response.success else "status: False"
                logger.info(log_entry)

            return response
        except MangroveException as exception:
            submission.update(status=False, errors=exception.message, is_test_mode=form_model.is_in_test_mode())
            raise

    def edit_survey_response(self):
        pass

    def delete_survey_response(self):
        pass

#class EntityService:
#    def save_entity(self):
#        pass
#
#
#    def edit_entity(self):
#        pass
#
#
#    def delete_entity(self ):
#        pass
