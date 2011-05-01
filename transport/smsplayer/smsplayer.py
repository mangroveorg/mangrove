# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
class SMSPlayer(object):
    def __init__(self):
        pass

    def parse(self,message):
        tokens = message.split("+")
        form_code = tokens[0].strip()
        tokens.remove(tokens[0])
        submission = {}
        for token in tokens:
            answer = token.split()
            field_code = answer[0]
            answer.remove(field_code)
            answer = "".join(answer)
            submission[field_code] = answer
        return form_code, submission



