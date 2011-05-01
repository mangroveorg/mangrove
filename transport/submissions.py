# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
Common entry point for all submissions to Mangrove via multiple channels.
Will log the submission and forward to the appropriate channel handler.
"""
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.datastore import entity
from mangrove.datastore import reporter
from mangrove.errors.MangroveException import MangroveException
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
    def __init__(self, message, success, submission_id):
        self.message = message
        self.success = success
        self.submission_id = submission_id


class UnknownTransportException(MangroveException):
    pass


class SubmissionHandler(object):
    def __init__(self, dbm):
        self.dbm = dbm

    def accept(self, request):
        assert request is not None
        from_number = request.source
        submission_id = self.dbm.save(SubmissionLogDocument(channel = request.transport,source = from_number,
                                            destination =request.destination,message=request.message))

        reporter.check_is_registered(self.dbm,from_number)
        player = self.get_player_for_transport(request)
        form_code,values = player.parse(request.message)
        form = form_model.get_questionnaire(self.dbm,form_code)
        form_submission = FormSubmission(form,values)
        if form_submission.is_valid():
            e = entity.get_by_short_code(self.dbm, form_submission.entity_id)
            e.add_data(data = form_submission.values.items(),submission_id = submission_id)
        return Response("",True,"")

    def get_player_for_transport(self, request):
        if request.transport == "sms":
            return SMSPlayer(self.dbm)
        else:
            raise UnknownTransportException(("No handler defined for transport %s") % request.transport)
