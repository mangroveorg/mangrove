# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore import reporter
from mangrove.errors.MangroveException import NumberNotRegisteredException
from mangrove.utils.types import is_not_empty, is_empty
from mangrove.datastore import entity
from mangrove.datastore import data
from mangrove.datastore import submission_api

def submit(dbm,text, from_number, to_number):
    assert is_not_empty(text) and is_not_empty(from_number) and is_not_empty(to_number)
    reporter.check_is_registered(dbm, from_number)
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
    return submission_api.submit(dbm,questionnaire_code,submission,"sms")


def get_from_reporter(dbm,from_number):
    reporters = data.fetch(dbm, entity_type=["Reporter"],
                            aggregates={"telephone_number": data.reduce_functions.LATEST,"first_name":data.reduce_functions.LATEST}
                          )
    from_reporter_list= [reporters[x] for x in reporters if reporters[x]["telephone_number"]==from_number]
    if len(from_reporter_list) != 1:
        raise NumberNotRegisteredException("Sorry, This number is not registered with us")
    return from_reporter_list[0]


class SMSPlayer(object):
    def __init__(self, dbm):
        self.dbm = dbm

    def parse(self,message):
        return "form_code",{}
