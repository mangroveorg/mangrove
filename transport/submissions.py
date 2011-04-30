# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
Common entry point for all submissions to Mangrove via multiple channels.
Will log the submission and forward to the appropriate channel handler.
"""
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.errors.MangroveException import MangroveException
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
        player = self.get_player(request)
        reporter = request.source
        destination = request.destination
        raw_message = request.message
        self.dbm.save(SubmissionLogDocument(channel = request.transport,source = reporter,
                                            destination = destination,message=raw_message))
        return Response("",True,"")

    def get_player(self, request):
        if request.transport == "sms":
            return SMSPlayer(self.dbm)
        else:
            raise UnknownTransportException(("No handler defined for transport %s") % request.transport)
