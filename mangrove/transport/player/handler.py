# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore.entity import delete_entity
from mangrove.transport.player.parser import DeleteRequestParser
from mangrove.transport.submissions import Submission

class DeleteHandler(object):
    def __init__(self, dbm):
        self.parser = DeleteRequestParser()
        self.dbm = dbm

    def handle(self, request):
        command, values = self.parser.parse(request.message)
        submission = Submission(self.dbm, request.transport, command, values)
        submission.save()
        delete_entity(self.dbm, values['entity_type'], values['entity_id'])

