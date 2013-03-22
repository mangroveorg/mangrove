class Channel(object):
    SMS = "sms"
    WEB = "web"
    XFORMS = "xforms"
    CSV = "csv"
    XLS = "xls"

class TransportInfo(object):
    def __init__(self, transport, source, destination):
        assert transport is not None
        assert source is not None
        assert destination is not None
        self.transport = transport
        self.source = source
        self.destination = destination
