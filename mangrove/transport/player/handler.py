# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.contrib.deletion import ENTITY_DELETION_FORM_CODE
from mangrove.datastore.entity import void_entity
from mangrove.form_model.form_model import FormSubmissionFactory, ENTITY_TYPE_FIELD_CODE, SHORT_CODE, REGISTRATION_FORM_CODE, GlobalRegistrationFormSubmission, DataFormSubmission
from mangrove.transport.facade import Response
from mangrove.utils.types import is_empty
from mangrove.transport.facade import create_response_from_form_submission

class SubmissionHandler(object):
    def __init__(self, dbm):
        self.dbm = dbm

    def handle(self, form_model, cleaned_data, errors, submission_uuid, reporter_names, location_tree, submission=None):
        form_submission = FormSubmissionFactory().get_form_submission(form_model, cleaned_data, errors,
            location_tree=location_tree)
        if form_submission.is_valid:
            form_submission.save(self.dbm)
        return create_response_from_form_submission(reporters=reporter_names, submission_id=submission_uuid,
            form_submission=form_submission)


class UpdateSubmissionHandler(object):
    def __init__(self, dbm):
        self.dbm = dbm

    def handle(self, form_model, cleaned_data, errors, reporter_names, location_tree, submission):
        submission_form = DataFormSubmission(form_model, cleaned_data, errors)
        submission_form.update_existing_data_records(self.dbm, submission.data_record)
        for key, value in form_model.submission.iteritems():
            submission.values[key] = value
        return create_response_from_form_submission(reporters=reporter_names, submission_id=submission.uuid,
            form_submission=submission)

# Looks like its only doing delete of what comes in GlobalRegistration?? Why would someone name it EditRegistrationHandler???
class EditRegistrationHandler(object):
    def __init__(self, dbm):
        self.dbm = dbm

    def handle(self, form_model, cleaned_data, errors, submission_uuid, reporter_names, location_tree, submission=None):
        form_submission = FormSubmissionFactory().get_form_submission(form_model, cleaned_data, errors,
            location_tree=location_tree)
        if form_submission.is_valid:
            if isinstance(form_submission, GlobalRegistrationFormSubmission):
                form_submission.void_existing_data_records(self.dbm)
                form_submission.update_location_and_geo_code(self.dbm)
            form_submission.update(self.dbm)
        return create_response_from_form_submission(reporters=reporter_names, submission_id=submission_uuid,
            form_submission=form_submission)

# Looks like its only doing delete of submissions?? Why would someone name it EditSubjectRegistrationHandler???
class EditSubjectRegistrationHandler(object):
    def __init__(self, dbm):
        self.dbm = dbm

    def handle(self, form_model, cleaned_data, errors, submission_uuid, reporter_names, location_tree, submission=None):
        form_submission = FormSubmissionFactory().get_form_submission(form_model, cleaned_data, errors,
            location_tree=location_tree)
        if form_submission.is_valid:
            form_submission.void_existing_data_records(self.dbm, form_model.form_code)
            form_submission.update(self.dbm)
        return create_response_from_form_submission(reporters=reporter_names, submission_id=submission_uuid,
            form_submission=form_submission)


class DeleteHandler(object):
    def __init__(self, dbm):
        self.dbm = dbm

    def handle(self, form_model, cleaned_data, errors, submission_uuid, reporter_names, location_tree=None,submission=None):
        short_code = cleaned_data[SHORT_CODE]
        entity_type = cleaned_data[ENTITY_TYPE_FIELD_CODE]
        if is_empty(errors):
            void_entity(self.dbm, entity_type, short_code)
        return Response(reporter_names, submission_uuid, is_empty(errors), errors, None, short_code, cleaned_data,
            False, entity_type, form_model.form_code)


def handler_factory(dbm, form_model, is_update=False):
    default_handler = SubmissionHandler
#    REGISTRATION_FORM_CODE is used when registering datasenders.
    if form_model.form_code == REGISTRATION_FORM_CODE and is_update:
        default_handler = EditRegistrationHandler
    elif form_model.is_registration_form and is_update:
        default_handler = EditSubjectRegistrationHandler
    handler_cls = handlers.get(form_model.form_code, default_handler)

    return handler_cls(dbm)

handlers = {
    ENTITY_DELETION_FORM_CODE: DeleteHandler
}
