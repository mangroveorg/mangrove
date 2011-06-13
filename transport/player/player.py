# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import csv
import re
from mangrove.errors.MangroveException import SMSParserInvalidFormatException, CSVParserInvalidHeaderFormatException, MangroveException
from mangrove.transport import reporter
from mangrove.transport.submissions import  SubmissionRequest, SubmissionResponse
from mangrove.utils.types import is_empty, is_string


class Channel(object):
    SMS = "sms"
    WEB = "web"
    XFORMS = "xforms"
    CSV = "csv"


class Request(object):
    def __init__(self, transport, message, source, destination):
        self.transport = transport
        self.message = message
        self.source = source
        self.destination = destination


class Response(object):
    def __init__(self, reporters, success, errors, submission_id=None, datarecord_id=None, short_code=None):
        self.reporters = reporters if reporters is not None else []
        self.success = success
        self.submission_id = submission_id
        self.errors = errors
        self.datarecord_id = datarecord_id
        self.short_code = short_code


class SMSPlayer(object):
    def __init__(self, dbm, submission_handler):
        self.dbm = dbm
        self.submission_handler = submission_handler

    def accept(self, request):
        assert request is not None
        assert request.source is not None
        assert request.destination is not None
        assert request.message is not None
        reporters = reporter.find_reporter(self.dbm, request.source)
        sms_parser = SMSParser()
        form_code, values = sms_parser.parse(request.message)
        submission_request = SubmissionRequest(form_code=form_code, submission=values, transport=request.transport,
                                               source=request.source, destination=request.destination)
        submission_response = self.submission_handler.accept(submission_request)
        return Response(reporters=reporters, success=submission_response.success, errors=submission_response.errors,
                        submission_id=submission_response.submission_id,
                        datarecord_id=submission_response.datarecord_id, short_code=submission_response.short_code)


class SMSParser(object):
    MESSAGE_PREFIX = r'^(\w+)\s+\+(\w+)\s+(\w+)'
    MESSAGE_TOKEN = r"(\S+)(.*)"
    SEPARATOR = "+"

    def __init__(self):
        pass

    def parse(self, message):
        message = message.strip()
        self._validate_message_format(message)
        tokens = message.split(self.SEPARATOR)
        form_code = tokens[0].strip()
        tokens.remove(tokens[0])
        #remove any space if any. for example if the message is +
        tokens = [token.strip() for token in tokens if token]
        submission = {}
        for token in tokens:
            if is_empty(token): continue
            field_code, answer = self._parse_token(token)
            field_code = field_code.lower()
            submission[field_code] = answer.strip()
        return form_code, submission

    def _parse_token(self, token):
        m = re.match(self.MESSAGE_TOKEN, token)  # Match first non white space set of values.
        return m.groups()

    def _validate_message_format(self, message):
        if not re.match(self.MESSAGE_PREFIX, message):
            raise SMSParserInvalidFormatException(message)


class WebPlayer(object):
    def __init__(self, dbm, submission_handler):
        self.dbm = dbm
        self.submission_handler = submission_handler

    def accept(self, request):
        assert request is not None
        assert request.source is not None
        assert request.destination is not None
        assert request.message is not None
        web_parser = WebParser()
        form_code, values = web_parser.parse(request.message)
        submission_request = SubmissionRequest(form_code=form_code, submission=values, transport=request.transport,
                                               source=request.source, destination=request.destination)
        submission_response = self.submission_handler.accept(submission_request)
        return Response(reporters=[], success=submission_response.success, errors=submission_response.errors,
                        submission_id=submission_response.submission_id,
                        datarecord_id=submission_response.datarecord_id, short_code=submission_response.short_code)


class WebParser(object):
    def parse(self, message):
        form_code = message.pop('form_code')
        return form_code, message


class CsvPlayer(object):
    def __init__(self, dbm, submission_handler, parser):
        self.dbm = dbm
        self.submission_handler = submission_handler
        self.parser = parser

    def accept(self, csv_data):
        response = []
        submissions = self.parser.parse(csv_data)
        for (form_code, values) in submissions:
            submission_request = SubmissionRequest(form_code=form_code, submission=values, transport=Channel.CSV,
                                                   source=Channel.CSV, destination="")
            try:
                submission_response = self.submission_handler.accept(submission_request)
                response.append(
                    Response(reporters=[], success=submission_response.success, errors=submission_response.errors,
                             submission_id=submission_response.submission_id,
                             datarecord_id=submission_response.datarecord_id,
                             short_code=submission_response.short_code))
            except MangroveException as e:
                response.append(Response(reporters=[], success=False, errors=e.message))
        return response


class CsvParser(object):
    def _next_line(self, dict_reader):
        return dict_reader.next().values()[0]

    def _parse_header(self, dict_reader):
        field_header = dict_reader.fieldnames
        while is_empty(field_header) or self._has_empty_values(field_header):
            try:
                field_header = self._next_line(dict_reader)
            except StopIteration:
                raise CSVParserInvalidHeaderFormatException()
        return [field.strip().lower() for field in field_header]

    def _strip_field_values(self, row):
        for key, value in row.items():
            if value is not None:
                row[key] = value.strip()

    def _parse_row(self, form_code_fieldname, row):
        result_row = dict(row)
        self._strip_field_values(result_row)
        form_code = result_row.pop(form_code_fieldname)
        return form_code, result_row

    def parse(self, csv_data):
        assert not is_string(csv_data)
        dict_reader = csv.DictReader(csv_data)
        dict_reader.fieldnames = self._parse_header(dict_reader)
        parsedData = []
        form_code_fieldname = dict_reader.fieldnames[0]
        for row in dict_reader:
            parsedData.append(self._parse_row(form_code_fieldname, row))
        return parsedData

    def _has_empty_values(self, values_list):
        for value in values_list:
            if is_empty(value):
                return True
        return False

