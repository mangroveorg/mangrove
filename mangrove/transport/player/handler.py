# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.errors.MangroveException import DataObjectNotFound
from mangrove.datastore.entity import invalidate_entity
from mangrove.transport.player.parser import DeleteRequestParser
from mangrove.transport.submissions import Submission

class DeleteHandler(object):
    def __init__(self, dbm, parser=None):
        self.parser = parser or DeleteRequestParser()
        self.dbm = dbm

    def handle(self, request):
        command, values = self.parser.parse(request.message)
        submission = Submission(self.dbm, request.transport, command, values)
        submission.save()
        try:
            invalidate_entity(self.dbm, values['entity_type'], values['entity_id'])
            submission.update(True,'')
        except DataObjectNotFound as exception:
            submission.update(False, exception.message)
            raise

