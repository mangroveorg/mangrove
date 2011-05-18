# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
Common entry point for all submissions to Mangrove via multiple channels.
Will log the submission and forward to the appropriate channel handler.
"""
from mangrove.datastore.datadict import DataDictType

from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.datastore import entity
from mangrove.datastore import reporter
from mangrove.datastore.entity import Entity
from mangrove.errors.MangroveException import MangroveException, FormModelDoesNotExistsException, NumberNotRegisteredException, EntityQuestionCodeNotSubmitted
from mangrove.form_model import form_model
from mangrove.form_model.form_model import FormSubmission, RegistrationFormSubmission
from mangrove.transport.player.player import SMSPlayer, WebPlayer
from mangrove.utils.types import is_string


class Request(object):
    def __init__(self, transport, message, source, destination):
        self.transport = transport
        self.message = message
        self.source = source
        self.destination = destination


class Response(object):
    SUCCESS_RESPONSE_TEMPLATE = "Thank You %s for your submission. The record id is - %s"
    ERROR_RESPONSE_TEMPLATE = "%s"

    def __init__(self, reporters, success, errors, submission_id=None, datarecord_id=None):
        self.success = success
        self.submission_id = submission_id
        self.errors = errors
        self.datarecord_id = datarecord_id
        if success:
            self.message = self._templatize_success_response_with_reporter_name_and_ids(reporters)
        else:
            self.message = self._templatize_error_response()

    def _templatize_success_response_with_reporter_name_and_ids(self, reporters):
        return Response.SUCCESS_RESPONSE_TEMPLATE % (reporters[0]["first_name"] if len(reporters) == 1 else "", self.datarecord_id)

    def _templatize_error_response(self):
        return Response.ERROR_RESPONSE_TEMPLATE % (", ".join(self.errors),)


class UnknownTransportException(MangroveException):
    pass


class SubmissionHandler(object):
    def __init__(self, dbm):
        self.dbm = dbm

    def update_submission_log(self, submission_id, status, errors):
        error_message = ""
        for each in errors:
            error_message = error_message + each + "\n"
        log = self.dbm._load_document(submission_id, SubmissionLogDocument)
        log.status = status
        log.error_message = log.error_message + (error_message or "")
        self.dbm._save_document(log)

    def accept(self, request):
        assert request is not None
        assert request.source is not None
        assert request.destination is not None
        assert request.message is not None
        reporters = []
        submission_id = None
        try:
            errors = []
            player = self.get_player_for_transport(request)
            form_code, values = player.parse(request.message)
            submission_id = self.dbm._save_document(
                SubmissionLogDocument(channel=request.transport, source=request.source,
                                      destination=request.destination, form_code=form_code, values=values,
                                      status=False, error_message="")).id
            form = form_model.get_form_model_by_code(self.dbm, form_code)
            if form.type == 'survey':
                reporters = reporter.find_reporter(self.dbm, request.source)
                form_submission = FormSubmission(form, values)
                if form_submission.is_valid():
                    e = entity.get_by_short_code(self.dbm, form_submission.short_code)
                    data_record_id = e.add_data(data=form_submission.values, submission_id=submission_id)
                    self.update_submission_log(submission_id, True, errors=[])
                    return Response(reporters, True, errors, submission_id, data_record_id)
                else:
                    errors.extend(form_submission.errors)
                    self.update_submission_log(submission_id, False, errors)
            elif form.type == 'registration':
                form_submission = RegistrationFormSubmission(form, values)
                if form_submission.is_valid():
                    entity_type = form.answers.get('entity_type')
                    short_code = entity.generate_entity_short_code(self.dbm, entity_type, suggested_id= form.answers.get("short_name"))
                    e = Entity(self.dbm, entity_type=entity_type, location=form.location, aggregation_paths=form.aggregation_paths, short_code=short_code)
                    e.save()
                    description_type = DataDictType(self.dbm, name='description Type', slug='description',
                                                    primitive_type='string')
                    mobile_number_type = DataDictType(self.dbm, name='Mobile Number Type', slug='mobile_number',
                                                      primitive_type='string')
                    description = form.answers.get("description")
                    mobile_number = form.answers.get("mobile_number")
                    data = [("description", description, description_type),
                            ("mobile_number", mobile_number, mobile_number_type),
                            ]
                    e.add_data(data=data, submission_id=submission_id)
                    self.update_submission_log(submission_id, True, errors=[])
#                   TODO: Get rid of the reporters from this
                    return Response([{'first_name': 'User'}], True, errors, submission_id,short_code)
                else:
                    errors.extend(form_submission.errors)
                    self.update_submission_log(submission_id, False, errors)

        except FormModelDoesNotExistsException as e:
            errors.append(e.message)
        except NumberNotRegisteredException as e:
            errors.append(e.message)
        except EntityQuestionCodeNotSubmitted as e:
            errors.append(e.message)
        return Response(reporters, False, errors, submission_id)

    def get_player_for_transport(self, request):
        if request.transport == "sms":
            return SMSPlayer()
        elif request.transport == 'web':
            return WebPlayer()
        else:
            raise UnknownTransportException(("No handler defined for transport %s") % request.transport)


def get_submissions_made_for_questionnaire(dbm, form_code, page_number=0, page_size=20, count_only=False):
    assert is_string(form_code)
    if count_only:
        rows = dbm.load_all_rows_in_view('mangrove_views/submissionlog', startkey=[form_code], endkey=[form_code, {}],
                                         group=True, group_level=1, reduce=True)
    else:
        rows = dbm.load_all_rows_in_view('mangrove_views/submissionlog', reduce=False, startkey=[form_code],
                                         endkey=[form_code, {}], skip=page_number * page_size, limit=page_size)
    return [each.value for each in rows]
