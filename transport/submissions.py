# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
Common entry point for all submissions to Mangrove via multiple channels.
Will log the submission and forward to the appropriate channel handler.
"""

from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.datastore import entity
from mangrove.datastore import reporter
from mangrove.errors.MangroveException import MangroveException, FormModelDoesNotExistsException, \
    NumberNotRegisteredException, EntityQuestionCodeNotSubmitted, ShortCodeAlreadyInUseException
from mangrove.form_model.form_model import get_form_model_by_code, LOCATION_TYPE_FIELD_NAME
from mangrove.transport.player.player import SMSPlayer, WebPlayer
from mangrove.utils.types import is_string


class Request(object):
    def __init__(self, transport, message, source, destination):
        self.transport = transport
        self.message = message
        self.source = source
        self.destination = destination


class Response(object):
    SUCCESS_RESPONSE_TEMPLATE = "Thank You %s for your submission."

    ERROR_RESPONSE_TEMPLATE = "%s"

    def __init__(self, reporters, success, errors, submission_id=None, datarecord_id=None,short_code = None,additional_text = None):
        self.reporters = reporters if reporters is not None else []
        self.success = success
        self.submission_id = submission_id
        self.errors = errors
        self.datarecord_id = datarecord_id
        if success:
            self.message = self._templatize_success_response(additional_text)
        else:
            self.message = self._templatize_error_response()
        self.short_code = short_code

    def _get_reporter_name(self):
        return self.reporters[0]["first_name"] if len(self.reporters) == 1 else ""

    def _templatize_success_response(self, additional_text):
        success_message = Response.SUCCESS_RESPONSE_TEMPLATE % (self._get_reporter_name())
        if additional_text:
            success_message += " " + additional_text
        return success_message

    def _templatize_error_response(self):
        return Response.ERROR_RESPONSE_TEMPLATE % (", ".join(self.errors),)


class UnknownTransportException(MangroveException):
    pass


class SubmissionLogger(object):

    def __init__(self,dbm):
        self.dbm = dbm

    def update_submission_log(self, submission_id, status, errors):
        error_message = ""
        for each in errors:
            error_message = error_message + each + "\n"
        log = self.dbm._load_document(submission_id, SubmissionLogDocument)
        log.status = status
        log.error_message = log.error_message + (error_message or "")
        self.dbm._save_document(log)

    def create_submission_log(self,channel, source, destination, form_code, values):
        return self.log(channel, source, destination, form_code, values,False,"")

    def log(self, channel, source, destination, form_code, values, status, error_message):
        return self.dbm._save_document(SubmissionLogDocument(channel=channel, source=source,
                                      destination=destination, form_code=form_code, values=values,
                                      status=status, error_message=error_message)).id

class SubmissionHandler(object):
    def __init__(self, dbm):
        self.dbm = dbm

    def accept(self, request):
        assert request is not None
        assert request.source is not None
        assert request.destination is not None
        assert request.message is not None
        reporters = []
        submission_id = None
        try:
            _errors = []
            player = self.get_player_for_transport(request)
            form_code, values = player.parse(request.message)
            logger = SubmissionLogger(self.dbm)
            submission_id = logger.create_submission_log(channel=request.transport,source=request.source,
                                                         destination=request.destination, form_code=form_code, values=values)
            form = get_form_model_by_code(self.dbm, form_code)
#                                             TODO: Fix reporter authorization based on channel.
            if request.transport.lower() == "web":
                reporters = None
            else:
                reporters = reporter.find_reporter(self.dbm, request.source)
            form_submission = form.validate_submission(values)
            if form_submission.is_valid:
                if form._is_registration_form():
                    e = entity.create_entity(dbm = self.dbm,
                                             entity_type=form_submission.entity_type,
#                                             TODO: Fix location values passed in after location story is played.
                                             location=[form_submission.cleaned_data.get(LOCATION_TYPE_FIELD_NAME)],
                                             aggregation_paths=None,
                                             short_code=form_submission.short_code
                    )
                    data_record_id = entity.add_data(dbm = self.dbm,short_code = e.short_code,
                                                     data=form_submission.values,submission_id=submission_id)
                    logger.update_submission_log(submission_id=submission_id, status=True, errors=[])
                    return Response(reporters, True, [], submission_id, data_record_id, e.short_code,
                                    additional_text=self._get_registration_text(e.short_code))
                else:
                    data_record_id = entity.add_data(dbm = self.dbm,short_code = form_submission.short_code,
                                                     data=form_submission.values,submission_id=submission_id)

                    logger.update_submission_log(submission_id=submission_id, status=True, errors=[])
                    return Response(reporters, True, [], submission_id, data_record_id)
            else:
                _errors.extend(form_submission.errors.values())
                logger.update_submission_log(submission_id=submission_id, status=False, errors=_errors)
        except FormModelDoesNotExistsException as e:
            _errors.append(e.message)
        except NumberNotRegisteredException as e:
            _errors.append(e.message)
        except EntityQuestionCodeNotSubmitted as e:
            _errors.append(e.message)
        except ShortCodeAlreadyInUseException as e:
            _errors.append(e.message)
        return Response(reporters, False, _errors, submission_id)

    def get_player_for_transport(self, request):
        if request.transport == "sms":
            return SMSPlayer()
        elif request.transport == 'web':
            return WebPlayer()
        else:
            raise UnknownTransportException(("No handler defined for transport %s") % request.transport)

    def _get_registration_text(self,short_code):
        RECORD_ID_TEMPLATE = "The short code is - %s"
        return RECORD_ID_TEMPLATE % (short_code,)


def get_submissions_made_for_questionnaire(dbm, form_code, page_number=0, page_size=20, count_only=False):
    assert is_string(form_code)
    if count_only:
        rows = dbm.load_all_rows_in_view('mangrove_views/submissionlog', startkey=[form_code], endkey=[form_code, {}],
                                         group=True, group_level=1, reduce=True)
    else:
        rows = dbm.load_all_rows_in_view('mangrove_views/submissionlog', reduce=False, startkey=[form_code],
                                         endkey=[form_code, {}], skip=page_number * page_size, limit=page_size)
    return [each.value for each in rows]
