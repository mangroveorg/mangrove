# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import SurveyResponseDocument
from mangrove.datastore.entity import DataRecord
from mangrove.utils.dates import convert_date_time_to_epoch
from mangrove.utils.types import is_string, sequence_to_str, is_sequence

ENTITY_QUESTION_DISPLAY_CODE = "q1"
SUCCESS_SURVEY_RESPONSE_VIEW_NAME = "success_survey_response"
UNDELETED_SURVEY_RESPONSE_VIEW_NAME = "undeleted_survey_response"
DELETED_SURVEY_RESPONSE_VIEW_NAME = "deleted_survey_response"

def survey_response_count(dbm, form_code, from_time, to_time, view_name="surveyresponse"):
    startkey, endkey = _get_start_and_end_key(form_code, from_time, to_time)
    rows = dbm.load_all_rows_in_view(view_name, descending=True, startkey=startkey, endkey=endkey)
    return len(rows) and rows[0]['value']['count']


def get_survey_responses(dbm, form_code, from_time, to_time, page_number=0, page_size=None,
                         view_name="surveyresponses"):
    startkey, endkey = _get_start_and_end_key(form_code, from_time, to_time)
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
    survey_responses = [SurveyResponse.new_from_doc(dbm=dbm, doc=SurveyResponse.__document_class__.wrap(row['value'])) for
                   row in
                   rows]
    return survey_responses[0] if survey_responses.__len__() > 0 else None


def survey_responses_by_form_code(dbm, form_code):
    return get_survey_responses(dbm, form_code, None, None)


def count_valid_web_survey_responses(dbm, form_code, from_time, to_time):
    startkey, endkey = _get_start_and_end_key(form_code, from_time, to_time)
    rows = dbm.load_all_rows_in_view('web_surveyresponse', descending=True, startkey=startkey, endkey=endkey)
    return 0 if len(rows) == 0 else rows[0]['value']['count']


def get_survey_responses_for_activity_period(dbm, form_code, from_time, to_time):
    from_time_in_epoch = convert_date_time_to_epoch(from_time) if from_time is not None else None
    to_time_in_epoch = convert_date_time_to_epoch(to_time) if to_time is not None else None
    startkey, endkey = _get_start_and_end_key(form_code, from_time_in_epoch, to_time_in_epoch)

    rows = dbm.load_all_rows_in_view('surveyresponse_for_activity_period', descending=True,
        startkey=startkey,
        endkey=endkey)
    return [SurveyResponse.new_from_doc(dbm=dbm, doc=SurveyResponse.__document_class__.wrap(row['value'])) for
                   row in
                   rows]


class SurveyResponse(DataObject):
    __document_class__ = SurveyResponseDocument

    def __init__(self, dbm, transport_info=None, form_code=None, form_model_revision=None, values=None):
        DataObject.__init__(self, dbm)
        if transport_info is not None:
            doc = SurveyResponseDocument(channel=transport_info.transport, source=transport_info.source,
                destination=transport_info.destination,
                form_code=form_code,
                form_model_revision=form_model_revision,
                values=values, status=False,
                error_message="", test=False)

            DataObject._set_document(self, doc)


    @property
    def data_record(self):
        return DataRecord.get(self._dbm, self._doc.data_record_id) if self._doc.data_record_id is not None else None

    @property
    def destination(self):
        return self._doc.destination

    @property
    def source(self):
        return self._doc.source

    @property
    def test(self):
        return self._doc.test

    @property
    def uuid(self):
        return self.id

    @property
    def status(self):
        return self._doc.status

    @property
    def channel(self):
        return self._doc.channel

    @property
    def form_code(self):
        return self._doc.form_code

    @property
    def form_model_revision(self):
        return self._doc.form_model_revision

    @property
    def values(self):
        return self._doc.values

    @property
    def errors(self):
        return self._doc.error_message

    @property
    def event_time(self):
        return self._doc.event_time

    def void(self, void=True):
        data_record_id = self._doc.data_record_id
        if data_record_id is not None:
            data_record = DataRecord.get(self._dbm, data_record_id)
            data_record.void(void)

        DataObject.void(self, void)

    def delete(self):
        data_record_id = self._doc.data_record_id
        if data_record_id is not None:
            data_record = DataRecord.get(self._dbm, data_record_id)
            data_record.delete()
        super(SurveyResponse, self).delete()

    def update(self, status, errors, data_record_id=None, is_test_mode=False):
        self._doc.status = status
        self._doc.data_record_id = data_record_id
        self._doc.error_message = self._to_string(errors)
        self._doc.test = is_test_mode
        self.save()

    def _to_string(self, errors):
        if is_string(errors):
            return errors
        if isinstance(errors, dict):
            return sequence_to_str(errors.values())
        if is_sequence(errors):
            return sequence_to_str(errors)
        return None


def _get_start_and_end_key(form_code, from_time, to_time):
    end = [form_code] if from_time is None else [form_code, from_time]
    start = [form_code, {}] if to_time is None else [form_code, to_time]

    return start, end