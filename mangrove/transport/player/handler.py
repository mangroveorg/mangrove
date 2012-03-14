# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.form_model.form_model import FormSubmissionFactory
from mangrove.transport.facade import Response


def handler_factory(dbm):
    return SubmissionHandler(dbm)

class SubmissionHandler(object):

    def __init__(self, dbm):
        self.dbm = dbm

    def handle(self, form_model, cleaned_data, errors, submission, reporter_names):
        form_submission = FormSubmissionFactory().get_form_submission(form_model, cleaned_data, errors)
        if form_submission.is_valid:
            form_submission.save(self.dbm)
        return Response(reporters=reporter_names, submission_id=submission.uuid,
        form_submission=form_submission)
