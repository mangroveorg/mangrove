
from mangrove.datastore.entity import  get_all_entities, Entity
# from mangrove.datastore.queries import get_entities_by_type

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
    rows = dbm.view.datasender_by_mobile(start_key=[from_number], end_key=[from_number,{},{}], include_docs=True)
    if (len(rows) == 0): raise NumberNotRegisteredException(from_number)
    return [Entity.new_from_doc(dbm=dbm, doc=Entity.__document_class__.wrap(row.get('doc'))) for row in rows]

def get_reporters_who_submitted_data_for_frequency_period(dbm, form_code, from_time=None, to_time=None):
    survey_responses = get_survey_responses_for_activity_period(dbm, form_code, from_time, to_time)
    source_owner_uids = set([survey_response.owner_uid for survey_response in survey_responses])
    all_reporters = get_entities_by_type(dbm, 'reporter')
    reporters = [reporter for reporter in all_reporters if reporter.id in source_owner_uids]
    return reporters
