# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.transport.player.parser import DeleteRequestParser

class DeleteHandler(object):
    def __init__(self, request):
        self.request = request
        self.parser = DeleteRequestParser()

    def handle(self):
        self.parser.parse(self.request.message)