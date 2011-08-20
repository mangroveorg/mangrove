# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.utils.types import is_string, sequence_to_str

ENTITY_QUESTION_DISPLAY_CODE = "eid"

class SubmissionLogger(object):
    def __init__(self, dbm):
        assert isinstance(dbm, DatabaseManager)
        self.dbm = dbm

    def void_data_record(self, submission_id):
        submission_log = self.dbm._load_document(submission_id, SubmissionLogDocument)
        submission_log.data_record_id = None
        submission_log.voided = True
        self.dbm._save_document(submission_log)

    def _to_string(self, errors):
        if is_string(errors):
            return errors
        if isinstance(errors, dict):
            return sequence_to_str(errors.values())
        return sequence_to_str(errors)

    def update_submission_log(self, submission_id, status, errors, data_record_id=None, in_test_mode=False):
        log = self.dbm._load_document(submission_id, SubmissionLogDocument)
        log.status = status
        log.voided = not status
        log.data_record_id = data_record_id
        log.error_message += self._to_string(errors)
        log.test = in_test_mode
        self.dbm._save_document(log)

    def create_submission_log(self, transportInfo,form_code,values,reporter_entity):
        return self.dbm._save_document(SubmissionLogDocument(channel=transportInfo.transport, source=transportInfo.source,
                                                             destination=transportInfo.destination,
                                                             form_code=form_code,
                                                             values=values, status=False,
                                                             error_message="", voided=True, test=False))

    def update_submission_log_from_form_submission(self, submission_id, form_submission):
        self.update_submission_log(submission_id,form_submission.saved,
                                   form_submission.errors,
                                   form_submission.data_record_id,
                                   form_submission.form_model.is_in_test_mode())


def _get_row_count(rows):
    if rows is None:
        return None
    result = rows[0].value
    return result.get('count') if result else None


def get_submission_count_for_form(dbm, form_code, start_time, end_time):
    assert is_string(form_code)
    start = [form_code] if start_time is  None else [form_code, start_time]
    end = [form_code,{}] if end_time  is None else [form_code, end_time, {}]
    rows = dbm.load_all_rows_in_view('submissionlog', startkey=start, endkey=end,
                                     group=True, group_level=1, reduce=True)
    count = _get_row_count(rows) if rows else 0
    return count


def get_submissions_made_for_form(dbm, form_code, start_time, end_time, page_number=0, page_size=20):
    assert is_string(form_code)
    end = [form_code] if start_time is  None else [form_code, start_time]
    start = [form_code,{}] if end_time  is None else [form_code, end_time, {}]
    if page_size is None:
        rows = dbm.load_all_rows_in_view('submissionlog', reduce=False, descending=True,
                                         startkey=start,
                                         endkey=end)
    else:
        rows = dbm.load_all_rows_in_view('submissionlog', reduce=False, descending=True,
                                         startkey=start,
                                         endkey=end, skip=page_number * page_size, limit=page_size)
    answers, ids = list(), list()
    for each in rows:
        answers.append(each.value)
        ids.append(each.value["data_record_id"])
    return answers, ids
