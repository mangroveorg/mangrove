# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.utils.types import is_not_empty, is_empty
from mangrove.datastore import form_model


def sumbit(dbm,text, from_number, to_number):
    assert is_not_empty(text) and is_not_empty(from_number) and is_not_empty(to_number)
    return parse(dbm,text)

def parse(dbm,text):
    messages = text.split("+")
    questionnaire_code=messages[0].strip()
    messages.remove(messages[0])
    submission = {}
    for message in messages:
        question_answer = message.split()
        question_code = question_answer[0]
        question_answer.remove(question_code)
        answer = "".join(question_answer)
        submission[question_code] = answer
    return form_model.submit(dbm,questionnaire_code,submission,"sms")