# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import re

class SMSPlayer(object):
    def __init__(self):
        pass

    def parse(self,message):
        tokens = message.split("+")
        form_code = tokens[0].strip()
        tokens.remove(tokens[0])
        submission = {}
        for token in tokens:
            field_code,answer = self._parse_token(token)
            submission[field_code] = answer.strip()
        return form_code, submission

    def _parse_token(self, token):
        m = re.match(r"(\S+)(.*)",token)  #Match first non white space set of values.
        return m.groups()




