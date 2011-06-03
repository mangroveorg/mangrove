# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import re
from mangrove.errors.MangroveException import SMSParserInvalidFormatException
from mangrove.utils.types import is_empty




class SMSPlayer(object):
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
        if not re.match(self.MESSAGE_PREFIX,message):
            raise SMSParserInvalidFormatException(message)


class WebPlayer(object):
    def __init__(self):
        pass

    def parse(self, message):
        form_code = message.pop('form_code')
        return form_code, message
