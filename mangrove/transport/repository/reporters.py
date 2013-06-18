# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore.entity import  get_all_entities
from mangrove.datastore.queries import get_entities_by_type

from mangrove.errors.MangroveException import NumberNotRegisteredException, MultipleReportersForANumberException
from mangrove.form_model.form_model import MOBILE_NUMBER_FIELD
from mangrove.transport.repository.survey_responses import get_survey_responses_for_activity_period

REPORTER_ENTITY_TYPE = ["reporter"]


def find_reporter(dbm, from_number):
    from_reporter_list = find_reporters_by_from_number(dbm, from_number)
    return [each.latest_values() for each in from_reporter_list]


def find_reporter_entity(dbm, from_number):
    reporter_list = find_reporters_by_from_number(dbm, from_number)
    if len(reporter_list) > 1:
        raise MultipleReportersForANumberException(from_number)
    return reporter_list[0]


def find_reporters_by_from_number(dbm, from_number):
    reporters = get_all_entities(dbm, entity_type=REPORTER_ENTITY_TYPE)

    def is_mobilenumber_same(reporter): return reporter.value(MOBILE_NUMBER_FIELD) == from_number


    from_reporter_list = filter(is_mobilenumber_same, reporters)

    if not len(from_reporter_list):
        raise NumberNotRegisteredException(from_number)
    return from_reporter_list


def get_reporters_who_submitted_data_for_frequency_period(dbm, form_code, from_time=None, to_time=None):
    survey_responses = get_survey_responses_for_activity_period(dbm, form_code, from_time, to_time)
    source_mobile_numbers = set([submission.origin for submission in survey_responses])
    all_reporters = get_entities_by_type(dbm, 'reporter')
    reporters = [reporter for reporter in all_reporters if reporter.value(MOBILE_NUMBER_FIELD) in source_mobile_numbers]
    return reporters
