# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from collections import OrderedDict
import csv
import re
import xlrd
from mangrove.errors.MangroveException import MultipleSubmissionsForSameCodeException, SMSParserInvalidFormatException,\
    CSVParserInvalidHeaderFormatException, XlsParserInvalidHeaderFormatException, SMSParserWrongNumberOfAnswersException
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.utils.types import is_empty, is_string


class SMSParserFactory(object):
    MESSAGE_PREFIX = ur'^(\w+)\s+\.(\w+)\s+(\w+)'
    def getSMSParser(self,message,dbm=None):
        clean_message = SMSParser().clean(message)
        if re.match(self.MESSAGE_PREFIX, clean_message,flags=re.UNICODE):
            return KeyBasedSMSParser()
        return OrderSMSParser(dbm)


class SMSParser(object):
    def _to_unicode(self, message):
        if type(message) is not unicode:
            message = unicode(message, encoding='utf-8')
        return message

    def clean(self, message):
        message = self._to_unicode(message)
        return message.strip()

    def validate_format(self, message_prefix_regex, message):
        if not re.match(message_prefix_regex, message, flags=re.UNICODE):
            raise SMSParserInvalidFormatException(message)

    def pop_form_code(self, tokens):
        form_code = tokens[0].strip().lower()
        tokens.remove(tokens[0])
        return form_code

    def parse(self, message):
        pass

    def form_code(self, message):
        pass



class KeyBasedSMSParser(SMSParser):
    MESSAGE_PREFIX = ur'^(\w+)\s+\.(\w+)\s+(\w+)'
    MESSAGE_TOKEN = ur"(\S+)(.*)"
    SEPARATOR = u" ."



    def _handle_tokens_with_only_separators(self, tokens):
        new_tokens = []
        for token in tokens:
            if is_empty(token): continue
            if is_empty("".join(token.split("."))): continue
            new_tokens.append(token.strip())
        return new_tokens

    def _parse_tokens(self, tokens):
        tokens = self._handle_tokens_with_only_separators(tokens)
        submission = OrderedDict()
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


    def parse(self, message):
        assert is_string(message)
        form_code = None
        try:
            form_code,tokens = self.form_code(message)
            submission = self._parse_tokens(tokens)
        except SMSParserInvalidFormatException as ex:
            raise SMSParserInvalidFormatException(ex.data)
        except MultipleSubmissionsForSameCodeException as ex:
            raise MultipleSubmissionsForSameCodeException(ex.data[0])
        return form_code, submission

    def form_code(self, message):
        message = self.clean(message)
        self.validate_format(self.MESSAGE_PREFIX,message)
        tokens = message.split(self.SEPARATOR)
        form_code = self.pop_form_code(tokens)
        return form_code, tokens

class OrderSMSParser(SMSParser):
    MESSAGE_PREFIX_FOR_ORDERED_SMS = ur'^(\w+)\s+(\w+)'

    def __init__(self, dbm):
        self.dbm = dbm

    def _parse_ordered_tokens(self, tokens, question_codes):
        submission = OrderedDict()

        if len(tokens) != len(question_codes):
            print tokens
            print question_codes
            raise SMSParserWrongNumberOfAnswersException()

        for token_index in range(len(tokens)):
            token = tokens[token_index]
            if is_empty(token): continue
            submission[question_codes[token_index]] = token
        return submission

    def parse(self, message):
        assert is_string(message)
        try:
            form_code, tokens = self.form_code(message)
            question_codes = self._get_question_codes_from_couchdb(form_code)
            submission = self._parse_ordered_tokens(tokens, question_codes)
        except SMSParserInvalidFormatException as ex:
            raise SMSParserInvalidFormatException(ex.data)
        return form_code, submission

    def form_code(self, message):
        message = self.clean(message)
        self.validate_format(self.MESSAGE_PREFIX_FOR_ORDERED_SMS,message)
        tokens = message.split()
        form_code = self.pop_form_code(tokens)
        return form_code, tokens

    def _get_question_codes_from_couchdb(self,form_code):
        questionnaire_form = get_form_model_by_code(self.dbm, form_code)
        question_codes = []
        form_fields = questionnaire_form.fields
        if questionnaire_form.entity_type[0] == 'reporter':
            form_fields.remove(form_fields[0])
        for aField in form_fields:
            question_codes.append(aField.code)
        return question_codes

class WebParser(object):
    def _remove_csrf_token(self, message):
        if 'csrfmiddlewaretoken' in message:
            message.pop('csrfmiddlewaretoken')

    def _fetch_string_value(self, message):
        return {code: self._to_str(value) for code, value in message.iteritems()}

    def parse(self, message):
        form_code = message.pop('form_code')
        self._remove_csrf_token(message)
        return form_code, self._fetch_string_value(message)

    def _to_str(self, value):
        return "".join(value) if value is not None else None


class CsvParser(object):
    EXTRA_VALUES = "extra_values"

    def _next_line(self, dict_reader):
        return dict_reader.respond().values()[0]

    def _parse_header(self, dict_reader):
        field_header = dict_reader.fieldnames

        if is_empty(field_header):
            raise CSVParserInvalidHeaderFormatException()

        self._remove_trailing_empty_header_field(field_header)

        if self._has_empty_values(field_header):
            raise CSVParserInvalidHeaderFormatException()

        return [field.strip().lower() for field in field_header]

    def _strip_field_values(self, row):
        for key, value in row.items():
            if value is not None and is_string(value):
                row[unicode(key, encoding='utf-8')] = unicode(value.strip(), encoding='utf-8')

    def _parse_row(self, form_code_fieldname, row):
        result_row = dict(row)
        self._strip_field_values(result_row)
        self._remove_extra_field_values(result_row)
        form_code = result_row.pop(form_code_fieldname).lower()
        return form_code, result_row

    def parse(self, csv_data):
        assert is_string(csv_data)
        csv_data = self._clean(csv_data)
        dict_reader = csv.DictReader(self._to_list(csv_data), restkey=self.EXTRA_VALUES)
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

    def _remove_trailing_empty_header_field(self, field_header):
        for field in field_header[::-1]:
            if is_empty(field):
                field_header.pop()
            else:
                break

    def _remove_extra_field_values(self, result_row):
        if result_row.get(self.EXTRA_VALUES):
            result_row.pop(self.EXTRA_VALUES)

    def _clean(self, csv_data):
        return csv_data.strip()

    def _to_list(self, csv_data):
        return csv_data.splitlines()


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

    def _remove_trailing_empty_header_field(self, field_header):
        for field in field_header[::-1]:
            if is_empty(field):
                field_header.pop()
            else:
                break

    def _is_header_row(self, row):
        if is_empty(row[0]):
            return None, False
        self._remove_trailing_empty_header_field(row)
        return [unicode(value).strip().lower() for value in row], True

    def _clean(self, row):
        return [unicode(value).strip() for value in row]

    def _is_empty(self, row):
        return len([value for value in row if not is_empty(value)]) == 0