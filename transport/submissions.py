# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.datastore.entity import DataRecord
from mangrove.utils.types import is_string, sequence_to_str, is_sequence

ENTITY_QUESTION_DISPLAY_CODE = "eid"

def submission_count(dbm, form_code, from_time, to_time):
    startkey, endkey = _get_start_and_end_key(form_code, from_time, to_time)
    rows = dbm.load_all_rows_in_view('submissionlog', descending=True, startkey=startkey, endkey = endkey )
    return 0 if len(rows) == 0 else rows[0]['value']['count']

def get_submissions(dbm, form_code, from_time, to_time, page_number=0, page_size=None):
    startkey, endkey = _get_start_and_end_key(form_code, from_time, to_time)
    if page_size is None:
        rows = dbm.load_all_rows_in_view('submissionlog', reduce=False, descending=True,
                                         startkey=startkey,
                                         endkey=endkey)
    else:
        rows = dbm.load_all_rows_in_view('submissionlog', reduce=False, descending=True,
                                         startkey=startkey,
                                         endkey=endkey, skip=page_number * page_size, limit=page_size)
    submissions = [Submission.new_from_doc(dbm=dbm, doc = Submission.__document_class__.wrap(row['value'])) for row in rows]
    return submissions

class Submission(DataObject):

    __document_class__ = SubmissionLogDocument

    def __init__(self, dbm, transport_info=None, form_code=None, values=None):
        DataObject.__init__(self, dbm)
        if transport_info is not None:
            doc = SubmissionLogDocument(channel=transport_info.transport, source=transport_info.source,
                                      destination=transport_info.destination,
                                      form_code=form_code,
                                      values=values, status=False,
                                      error_message="", test=False)

            DataObject._set_document(self, doc)

    @property
    def data_record_id(self):
        return self._doc.data_record_id

    @property
    def data_record(self):
        return DataRecord.get(self._dbm, self._doc.data_record_id) if self._doc.data_record_id is not None else None

    @property
    def destination(self):
        return self._doc.destination

    @property
    def source(self):
        return self._doc.source if not self._doc.test else "TEST"

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
    def values(self):
        return self._doc.values

    @property
    def errors(self):
        return self._doc.error_message

    def void(self):
        data_record_id = self._doc.data_record_id
        if data_record_id is not None:
            data_record = DataRecord.get(self._dbm, data_record_id)
            data_record.void()

        self._doc.data_record_id = None #This is because the existing functionality that when you void a submission it's link with a data record is dis-associated.
        self._doc.void = True
        self.save()

    def delete(self):
        data_record_id = self._doc.data_record_id
        if data_record_id is not None:
            data_record = DataRecord.get(self._dbm, data_record_id)
            data_record.delete()
        super(Submission, self).delete()

    def update(self, status, errors, data_record_id = None, is_test_mode = False):
        self._doc.status = status
        self._doc.void = not status
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
    end = [form_code] if from_time is  None else [form_code, from_time]
    start = [form_code,{}] if to_time  is None else [form_code, to_time]
    return start, end