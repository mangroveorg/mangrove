# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.errors.MangroveException import NumberNotRegisteredException
from mangrove.utils.types import is_not_empty, is_empty
from mangrove.datastore import form_model
from mangrove.datastore import entity
from mangrove.datastore import datarecord

def submit(dbm,text, from_number, to_number):
    assert is_not_empty(text) and is_not_empty(from_number) and is_not_empty(to_number)
    check_reporter_is_registered(dbm, from_number)
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

def check_reporter_is_registered(dbm, from_number):
    reporter_list = entity.get_entities_by_type(dbm, "Reporter")
    number_list = []
    for reporter in reporter_list:
        reporter_data = reporter.get_all_data()
        number_list.extend([data["data"]["telephone_number"]["value"]for data in reporter_data])
    if from_number not in number_list:
        raise NumberNotRegisteredException("Sorry, This number is not registered with us")