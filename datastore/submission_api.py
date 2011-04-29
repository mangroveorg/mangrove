import datarecord
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.field import field_attributes
from mangrove.errors.MangroveException import FieldDoesNotExistsException, EntityQuestionCodeNotSubmitted
from mangrove.form_model.form_model import get_questionnaire, get_entity_question_code


def _get_entity_id(dbm, entity_instance_short_id):
    return entity_instance_short_id


def _get_entity_instance_id(answers, dbm, entity_question_code):
    if answers.get(entity_question_code):
        entity_instance_short_id = answers.pop(entity_question_code)
        entity_instance_id = _get_entity_id(dbm, entity_instance_short_id)
    else:
        raise EntityQuestionCodeNotSubmitted()
    return entity_instance_id


def submit(dbm, questionnaire_code, answers, channel):
    assert isinstance(dbm, DatabaseManager)

    assert answers and channel and questionnaire_code

    field_name_list = []
    questionnaire = get_questionnaire(dbm, questionnaire_code)

    entity_question_code = get_entity_question_code(dbm, questionnaire_code)

    entity_instance_id = _get_entity_instance_id(answers, dbm, entity_question_code)

    for answer in answers:
        question = filter(lambda x:x.get('question_code') == answer, questionnaire.fields)
        if not len(question):
            raise FieldDoesNotExistsException(answer)
        else:
            field_name_list.append((question[0].get(field_attributes.NAME), answers[answer]))

    if entity_instance_id is not None:
        data_record_id = datarecord.submit(dbm, entity_instance_id, field_name_list, channel)[0]
        return data_record_id

    return None
