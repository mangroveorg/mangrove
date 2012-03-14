# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.contrib.deletion import ENTITY_DELETION_FORM_CODE
from mangrove.datastore.entity import invalidate_entity
from mangrove.form_model.form_model import FormSubmissionFactory, ENTITY_TYPE_FIELD_CODE, SHORT_CODE
from mangrove.transport.facade import Response
from mangrove.utils.types import is_empty
from mangrove.transport.facade import create_response_from_form_submission

class SubmissionHandler(object):

    def __init__(self, dbm):
        self.dbm = dbm

    def handle(self, form_model, cleaned_data, errors, submission, reporter_names):
        form_submission = FormSubmissionFactory().get_form_submission(form_model, cleaned_data, errors)
        if form_submission.is_valid:
            form_submission.save(self.dbm)
        return create_response_from_form_submission(reporters=reporter_names, submission_id=submission.uuid,
        form_submission=form_submission)

class DeleteHandler(object):

    def __init__(self, dbm):
        self.dbm = dbm

    def handle(self, form_model, cleaned_data, errors, submission, reporter_names):
        short_code = cleaned_data[SHORT_CODE]
        entity_type = cleaned_data[ENTITY_TYPE_FIELD_CODE]
        if is_empty(errors):
            invalidate_entity(self.dbm, entity_type, short_code)
        return Response(reporter_names, submission.uuid, is_empty(errors), errors, None, short_code, cleaned_data,
            False, entity_type, form_model.form_code)

def handler_factory(dbm, form_code):
    handler_cls = handlers.get(form_code, SubmissionHandler)
    return handler_cls(dbm)

handlers = {
    ENTITY_DELETION_FORM_CODE : DeleteHandler
}
