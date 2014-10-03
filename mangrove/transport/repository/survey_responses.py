
from mangrove.utils.dates import convert_date_time_to_epoch
from mangrove.transport.contract.survey_response import SurveyResponse

ENTITY_QUESTION_DISPLAY_CODE = "q1"
# SUCCESS_SURVEY_RESPONSE_VIEW_NAME = "success_survey_response"
UNDELETED_SURVEY_RESPONSE_VIEW_NAME = "undeleted_survey_response"
# DELETED_SURVEY_RESPONSE_VIEW_NAME = "deleted_survey_response"

def survey_response_count(dbm, form_model_id, from_time, to_time, view_name="surveyresponse"):
    startkey, endkey = _get_start_and_end_key(form_model_id, from_time, to_time)
    rows = dbm.load_all_rows_in_view(view_name, descending=True, startkey=startkey, endkey=endkey)
    return len(rows) and rows[0]['value']['count']


def get_survey_responses(dbm, form_model_id, from_time, to_time, page_number=0, page_size=None,
                         view_name="surveyresponse"):
    startkey, endkey = _get_start_and_end_key(form_model_id, from_time, to_time)
    if page_size is None:
        rows = dbm.load_all_rows_in_view(view_name, reduce=False, descending=True,
            startkey=startkey,
            endkey=endkey)
    else:
        rows = dbm.load_all_rows_in_view(view_name, reduce=False, descending=True,
            startkey=startkey,
            endkey=endkey, skip=page_number * page_size, limit=page_size)
    return [SurveyResponse.new_from_doc(dbm=dbm, doc=SurveyResponse.__document_class__.wrap(row['value'])) for row in
            rows]


def get_survey_response_by_id(dbm, survey_response_id):
    rows = dbm.load_all_rows_in_view("survey_response_by_survey_response_id", key=survey_response_id)
    survey_responses = [SurveyResponse.new_from_doc(dbm=dbm, doc=SurveyResponse.__document_class__.wrap(row['value']))
                        for
                        row in
                        rows]
    return survey_responses[0] if survey_responses.__len__() > 0 else None

def get_survey_response_document(dbm, survey_response_id):
    return  dbm._load_document(survey_response_id)


def survey_responses_by_form_model_id(dbm, form_model_id):
    return get_survey_responses(dbm, form_model_id, None, None)


# def count_valid_web_survey_responses(dbm, form_code, from_time, to_time):
#     startkey, endkey = _get_start_and_end_key(form_code, from_time, to_time)
#     rows = dbm.load_all_rows_in_view('web_surveyresponse', descending=True, startkey=startkey, endkey=endkey)
#     return 0 if len(rows) == 0 else rows[0]['value']['count']


def get_survey_responses_for_activity_period(dbm, form_model_id, from_time, to_time):
    from_time_in_epoch = convert_date_time_to_epoch(from_time) if from_time is not None else None
    to_time_in_epoch = convert_date_time_to_epoch(to_time) if to_time is not None else None
    startkey, endkey = _get_start_and_end_key(form_model_id, from_time_in_epoch, to_time_in_epoch)

    rows = dbm.load_all_rows_in_view('survey_response_for_activity_period', descending=True,
        startkey=startkey,
        endkey=endkey)
    return [SurveyResponse.new_from_doc(dbm=dbm, doc=SurveyResponse.__document_class__.wrap(row['value'])) for
            row in
            rows]

def _get_start_and_end_key(form_model_id, from_time, to_time):
    end = [form_model_id] if from_time is None else [form_model_id, from_time]
    start = [form_model_id, {}] if to_time is None else [form_model_id, to_time]

    return start, end