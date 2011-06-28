# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import csv
import re
import xlrd
from mangrove.errors.MangroveException import SMSParserInvalidFormatException, CSVParserInvalidHeaderFormatException, MangroveException, MultipleSubmissionsForSameCodeException
from mangrove.transport import reporter
from mangrove.transport.submissions import  SubmissionRequest
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
    def __init__(self, reporters, success, errors, submission_id=None, datarecord_id=None, short_code=None,
                 processed_data=None):
        self.reporters = reporters if reporters is not None else []
        self.success = success
        self.submission_id = submission_id
        self.errors = errors
        self.datarecord_id = datarecord_id
        self.short_code = short_code
        self.processed_data = processed_data


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
                        datarecord_id=submission_response.datarecord_id, short_code=submission_response.short_code,
                        processed_data=submission_response.processed_data)


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
        form_code = tokens[0].strip().lower()
        tokens.remove(tokens[0])
        #remove any space if any. for example if the message is +
        tokens = [token.strip() for token in tokens if token]
        submission = {}
        for token in tokens:
            if is_empty(token): continue
            field_code, answer = self._parse_token(token)
            field_code = field_code.lower()
            if field_code in submission.keys():
                raise MultipleSubmissionsForSameCodeException(field_code)
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
                        datarecord_id=submission_response.datarecord_id, short_code=submission_response.short_code,
                        processed_data=submission_response.processed_data)


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
                if not submission_response.success:
                    response.append(Response(reporters=[], success=False,
                                             errors=dict(error=submission_response.errors.values(), row=values)))
                else:
                    response.append(
                        Response(reporters=[], success=submission_response.success, errors=submission_response.errors,
                                 submission_id=submission_response.submission_id,
                                 datarecord_id=submission_response.datarecord_id,
                                 short_code=submission_response.short_code))
            except MangroveException as e:
                response.append(Response(reporters=[], success=False, errors=dict(error=e.message, row=values)))
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
            if value is not None and type(value) is str:
                row[key] = value.strip()

    def _parse_row(self, form_code_fieldname, row):
        result_row = dict(row)
        self._strip_field_values(result_row)
        form_code = result_row.pop(form_code_fieldname).lower()
        return form_code, result_row

    def parse(self, csv_data):
        assert not is_string(csv_data)
        dict_reader = csv.DictReader(csv_data, restkey='extra_values')
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


class XlsPlayer(object):
    def __init__(self, dbm, submission_handler, parser):
        self.dbm = dbm
        self.submission_handler = submission_handler
        self.parser = parser

    def accept(self, file_contents):
        pass


class XlsParser(object):
    def parse(self, xls_contents):
        assert xls_contents is not None
        workbook = xlrd.open_workbook(file_contents=xls_contents)
        worksheet = workbook.sheets()[0]
        header_found = False
        header = None
        parsedData = []
        for row_num in range(worksheet.nrows):
            row = worksheet.row_values(row_num)

            if not header_found:
                header,header_found = self._is_header_row(row)
                continue
            if self._is_empty(row):
                continue

            row = self._clean(row)
            row_dict = dict(zip(header,row))
            form_code,values = (row_dict.pop(header[0]), row_dict)
            parsedData.append((form_code,values))
        return parsedData


    def _is_header_row(self, row):
        if is_empty(row[0]):
            return None,False
        return self._clean(row),True

    def _clean(self, row):
        return [str(value).strip() for value in row]

    def _is_empty(self, row):
        return len([ value for value in row if not is_empty(value)]) == 0



        