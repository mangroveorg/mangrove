# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import csv
import pprint
import time
import re
import xlrd
from mangrove.errors.MangroveException import SMSParserInvalidFormatException, CSVParserInvalidHeaderFormatException, MangroveException, MultipleSubmissionsForSameCodeException, XlsParserInvalidHeaderFormatException
from mangrove.form_model.form_model import get_form_model_by_code, ENTITY_TYPE_FIELD_CODE
from mangrove.transport import reporter
from mangrove.transport.submissions import  SubmissionRequest
from mangrove.utils.types import is_empty, is_string


class Channel(object):
    SMS = "sms"
    WEB = "web"
    XFORMS = "xforms"
    CSV = "csv"
    XLS = "xls"


class TransportInfo(object):
    def __init__(self,transport, source, destination):
        assert transport is not None
        assert source is not None
        assert destination is not None
        self.transport = transport
        self.source = source
        self.destination = destination


class Request(object):
    def __init__(self, message, transportInfo):
        assert transportInfo is not None
        assert message is not None
        self.transport = transportInfo
        self.message = message


class Response(object):
    def __init__(self, reporters, submission_response):
        self.reporters = reporters if reporters is not None else []
        self.success = False
        self.errors = {}
        if submission_response is not None:
            self.success = submission_response.success
            self.submission_id = submission_response.submission_id
            self.errors = submission_response.errors
            self.datarecord_id = submission_response.datarecord_id
            self.short_code = submission_response.short_code
            self.processed_data = submission_response.processed_data


def _short_code_not_in(entity_q_code,values):
    return values.get(entity_q_code) is None


def _epoch_last_three_digit():
    epoch = long(time.time() * 100)
    epoch_last_three_digit = divmod(epoch, 1000)[1]
    return epoch_last_three_digit

def _generate_short_code(entity_type):
    epoch_last_six_digit = _epoch_last_three_digit()
    return entity_type[:3].lower()+ str(epoch_last_six_digit)


def _generate_short_code_if_registration_form(dbm, form_code, values):


    form_model = get_form_model_by_code(dbm, form_code)
    if form_model.is_registration_form():
        entity_q_code = form_model.entity_question.code
        if _short_code_not_in(entity_q_code, values):
            values[entity_q_code] = _generate_short_code(values[ENTITY_TYPE_FIELD_CODE])


def submit( dbm,submission_handler, transportInfo, form_code, values):
    _generate_short_code_if_registration_form(dbm, form_code, values)
    submission_request = SubmissionRequest(form_code=form_code, submission=values, transport=transportInfo.transport,
                                           source=transportInfo.source, destination=transportInfo.destination)
    submission_response = submission_handler.accept(submission_request)
    return submission_response



class SMSPlayer(object):
    def __init__(self, dbm, submission_handler):
        self.dbm = dbm
        self.submission_handler = submission_handler

    def _parse(self, request):
        sms_parser = SMSParser()
        form_code, values = sms_parser.parse(request.message)
        return form_code, values

    def accept(self, request):
        assert request is not None
        reporters = reporter.find_reporter(self.dbm, request.transport.source)
        form_code, values = self._parse(request)
        submission_response = submit(self.dbm,self.submission_handler, request.transport, form_code, values)
        return Response(reporters=reporters, submission_response=submission_response)


class SMSParser(object):
    MESSAGE_PREFIX = ur'^(\w+)\s+\+(\w+)\s+(\w+)'
    MESSAGE_TOKEN = ur"(\S+)(.*)"
    SEPARATOR = u"+"

    def __init__(self):
        pass

    def _to_unicode(self, message):
        if type(message) is not unicode:
            message = unicode(message, encoding='utf-8')
        return message

    def _clean(self, message):
        message = self._to_unicode(message)
        return message.strip()

    def _pop_form_code(self, tokens):
        form_code = tokens[0].strip().lower()
        tokens.remove(tokens[0])
        return form_code

    def _parse_tokens(self, tokens):
        tokens = [token.strip() for token in tokens if token]
        submission = {}
        for token in tokens:
            if is_empty(token): continue
            field_code, answer = self._parse_token(token)
            if field_code in submission.keys():
                raise MultipleSubmissionsForSameCodeException(field_code)
            submission[field_code] = answer
        return submission

    def _parse_token(self, token):
        m = re.match(self.MESSAGE_TOKEN, token, flags=re.UNICODE)  # Match first non white space set of values.
        field_code, value = m.groups()
        return field_code.lower(), value.strip()

    def _validate_format(self, message):
        if not re.match(self.MESSAGE_PREFIX, message, flags=re.UNICODE):
            raise SMSParserInvalidFormatException(message)
    
    def parse(self, message):
        assert is_string(message)
        message = self._clean(message)
        self._validate_format(message)
        tokens = message.split(self.SEPARATOR)
        form_code = self._pop_form_code(tokens)
        submission = self._parse_tokens(tokens)
        return form_code, submission



class WebPlayer(object):
    def __init__(self, dbm, submission_handler):
        self.dbm = dbm
        self.submission_handler = submission_handler

    def _parse(self, request):
        web_parser = WebParser()
        form_code, values = web_parser.parse(request.message)
        return form_code, values

    def accept(self, request):
        assert request is not None
        form_code, values = self._parse(request)
        submission_response = submit(self.dbm,self.submission_handler, request.transport, form_code, values)
        return Response(reporters=[], submission_response=submission_response)


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
        responses = []
        submissions = self.parser.parse(csv_data)
        for (form_code, values) in submissions:
            try:
                transport_info = TransportInfo(transport=Channel.CSV, source=Channel.CSV, destination="")
                submission_response = submit(self.dbm,self.submission_handler, transport_info, form_code, values)
                response= Response(reporters=[],submission_response=submission_response)
                if not submission_response.success:
                    response.errors = dict(error=submission_response.errors.values(), row=values)
                responses.append(response)
            except MangroveException as e:
                response = Response(reporters=[], submission_response=None)
                response.success=False
                response.errors = dict(error=e.message, row=values)
                responses.append(response)
        return responses


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
            if value is not None and is_string(value):
                row[unicode(key, encoding='utf-8')] = unicode(value.strip(), encoding='utf-8')

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
        responses = []
        submissions = self.parser.parse(file_contents)
        for (form_code, values) in submissions:
            try:
                transport_info = TransportInfo(transport=Channel.XLS, source=Channel.XLS, destination="")
                submission_response = submit(self.dbm,self.submission_handler, transport_info, form_code, values)
                response= Response(reporters=[],submission_response=submission_response)
                if not submission_response.success:
                    response.errors = dict(error=submission_response.errors.values(), row=values)
                responses.append(response)
            except MangroveException as e:
                response = Response(reporters=[], submission_response=None)
                response.success=False
                response.errors = dict(error=e.message, row=values)
                responses.append(response)
        return responses


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
                header, header_found = self._is_header_row(row)
                continue
            if self._is_empty(row):
                continue

            row = self._clean(row)
            row_dict = dict(zip(header, row))
            form_code, values = (row_dict.pop(header[0]).lower(), row_dict)
            parsedData.append((form_code, values))
        if not header_found:
            raise XlsParserInvalidHeaderFormatException()
        return parsedData


    def _is_header_row(self, row):
        if is_empty(row[0]):
            return None, False
        return [str(value).strip().lower() for value in row], True

    def _clean(self, row):
        return [str(value).strip() for value in row]

    def _is_empty(self, row):
        return len([value for value in row if not is_empty(value)]) == 0



        