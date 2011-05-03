# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
Common entry point for all submissions to Mangrove via multiple channels.
Will log the submission and forward to the appropriate channel handler.
"""
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.datastore import entity
from mangrove.datastore import reporter
from mangrove.errors.MangroveException import MangroveException, FormModelDoesNotExistsException, NumberNotRegisteredException
from mangrove.form_model import form_model
from mangrove.form_model.form_model import FormSubmission
from mangrove.transport.smsplayer.smsplayer import SMSPlayer

class Request(object):
    def __init__(self, transport,message,source,destination):
        self.transport = transport
        self.message = message
        self.source = source
        self.destination = destination


class Response(object):
    def __init__(self, message, success, errors, submission_id = None,datarecord_id = None):
        self.message = message
        self.success = success
        self.submission_id = submission_id
        self.errors = errors
        self.datarecord_id = datarecord_id


class UnknownTransportException(MangroveException):
    pass


class SubmissionHandler(object):
    def __init__(self, dbm):
        self.dbm = dbm

    def accept(self, request):
        assert request is not None
        assert request.source is not None
        assert request.destination is not None
        assert request.message is not None
        try:
            errors = []
            submission_id = None
            submission_id = self.dbm.save(SubmissionLogDocument(channel = request.transport,source =request.source,
                                                destination =request.destination,message=request.message)).id
            reporter.find_reporter(self.dbm, request.source)
            player = self.get_player_for_transport(request)
            form_code,values = player.parse(request.message)
            form = form_model.get_questionnaire(self.dbm,form_code)
            form_submission = FormSubmission(form,values)
            if form_submission.is_valid():
                e = entity.get_by_short_code(self.dbm, form_submission.entity_id)
                data_record_id = e.add_data(data = form_submission.values.items(),submission_id = submission_id)
                return Response(request.message,True,errors,submission_id,data_record_id)
            else:
                errors.extend(form_submission.errors)
        except FormModelDoesNotExistsException as e:
            errors.append(e.message)
        except NumberNotRegisteredException as e:
            errors.append(e.message)
        return Response(request.message,False,errors,submission_id)

    def get_player_for_transport(self, request):
        if request.transport == "sms":
            return SMSPlayer()
        else:
            raise UnknownTransportException(("No handler defined for transport %s") % request.transport)
