from copy import copy
import traceback
from mangrove.datastore.entity import by_short_code
from mangrove.feeds.enriched_survey_response import EnrichedSurveyResponseBuilder
from mangrove.form_model.forms import EditSurveyResponseForm
from mangrove.form_model.form_submission import DataFormSubmission
from mangrove.errors.MangroveException import MangroveException
from mangrove.form_model.form_model import get_form_model_by_code, FormModel
from mangrove.form_model.project import Project
from mangrove.transport.contract.response import Response
from mangrove.transport.repository.reporters import REPORTER_ENTITY_TYPE
from mangrove.transport.repository.survey_responses import SurveyResponse


class SurveyResponseService(object):
    def __init__(self, dbm, logger=None, feeds_dbm=None, admin_id=None, response=None):
        self.dbm = dbm
        self.logger = logger
        self.feeds_dbm = feeds_dbm
        self.admin_id = admin_id
        self.response = response

    def save_survey(self, form_code, values, reporter_names, transport_info, reporter_id,
                    additional_feed_dictionary=None, translation_processor=None):
        form_model = get_form_model_by_code(self.dbm, form_code)

        #TODO : validate_submission should use form_model's bound values
        form_model.bind(values)
        cleaned_data, errors = form_model.validate_submission(values=values)

        if reporter_id is not None:
            survey_response = self.create_survey_response_from_known_datasender(transport_info, form_model,
                                                                            form_model.bound_values(),
                                                                            reporter_id, self.response)
        else:
            survey_response = self.create_survey_response_from_unknown_datasender(transport_info, form_model.id,
                                                                            form_model.bound_values(), self.response)

        survey_response.set_form(form_model)

        form_submission = DataFormSubmission(form_model, cleaned_data, errors)
        feed_create_errors = None
        try:
            if form_submission.is_valid:
                form_submission.save(self.dbm)

        except MangroveException as exception:
            errors = exception.message
            raise
        finally:
            if translation_processor is not None:
                translated_errors = translation_processor(form_model, self.response).process()
                survey_response.set_status(translated_errors)
            else:
                survey_response.set_status(errors)
            survey_response.create(form_submission.data_record_id)
            try:
                if self.feeds_dbm:
                    builder = EnrichedSurveyResponseBuilder(self.dbm, survey_response, form_model,
                                                            additional_feed_dictionary)
                    event_document = builder.feed_document()
                    self.feeds_dbm._save_document(event_document)
            except Exception as e:
                feed_create_errors = 'error while creating feed doc for %s \n' % survey_response.id
                feed_create_errors += e.message + '\n'
                feed_create_errors += traceback.format_exc()
        if self.response is None:
            errors = form_submission.errors
            success = form_submission.saved
        else:
            errors = self.response.errors
            success = False

        return Response(reporter_names,  survey_response.uuid, success,
                        errors, form_submission.data_record_id, form_submission.short_code,
                        form_submission.cleaned_data, form_submission.is_registration, form_submission.entity_type,
                        form_submission.form_model.form_code, feed_create_errors, created=survey_response.created,
                        version=survey_response.version)

    def edit_survey(self, form_code, values, reporter_names,  survey_response,
                    additional_feed_dictionary=None, owner_id=None):
        form_model = get_form_model_by_code(self.dbm, form_code)

        form = EditSurveyResponseForm(self.dbm, survey_response, form_model, values)
        try:
            if form.is_valid:
                if owner_id:
                    reporter = by_short_code(self.dbm, owner_id, REPORTER_ENTITY_TYPE)
                    survey_response.owner_uid = reporter.id
                survey_response.modified_by = self.admin_id or owner_id
                survey_response = form.save()
            try:
                feed_create_errors = None
                if self.feeds_dbm:
                    builder = EnrichedSurveyResponseBuilder(self.dbm, survey_response, form_model,
                                                            additional_feed_dictionary)
                    event_document = builder.update_event_document(self.feeds_dbm)
                    self.feeds_dbm._save_document(event_document)
            except Exception as e:
                feed_create_errors = 'error while editing feed doc for %s \n' % survey_response.id
                feed_create_errors += e.message + '\n'
                feed_create_errors += traceback.format_exc()

        except MangroveException as exception:
            raise
        return Response(reporter_names,  survey_response.uuid, form.saved,
                        form.errors, form.data_record_id, None,
                        form._cleaned_data, form.is_registration, form.entity_type,
                        form.form_model.form_code, feed_create_errors, created=survey_response.created,
                        version=survey_response.version)

    def delete_survey(self, survey_response, additional_details):
        feed_delete_errors = None
        try:
            survey_response.void()
            form_model = FormModel.get(self.dbm,survey_response.form_model_id)
            if self.feeds_dbm:
                feed_delete_errors = EnrichedSurveyResponseBuilder(self.dbm, survey_response, form_model,
                                                                   additional_details).delete_feed_document(
                    self.feeds_dbm)
        except MangroveException as e:
            return Response(errors=e.message, feed_error_message=feed_delete_errors)
        return Response(success=True, feed_error_message=feed_delete_errors)


    def create_survey_response_from_known_datasender(self, transport_info, form_model, values, reporter_id, response):
        reporter = by_short_code(self.dbm, reporter_id.lower(), REPORTER_ENTITY_TYPE)
        owner_uid = reporter.id
        survey_response = SurveyResponse(self.dbm, transport_info, form_model.id, values=values, owner_uid=owner_uid,
                                         admin_id=self.admin_id or reporter_id, response=response)
        project = Project.from_form_model(form_model)
        if reporter_id not in project.data_senders:
            survey_response.is_anonymous_submission = True
        return survey_response


    def create_survey_response_from_unknown_datasender(self, transport_info, form_model_id, values, response):
        survey_response = SurveyResponse(self.dbm, transport_info, form_model_id, values=values, owner_uid=None,
                                         admin_id=self.admin_id or transport_info.source, response=response)
        survey_response.is_anonymous_submission = True
        return survey_response
