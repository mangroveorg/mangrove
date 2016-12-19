from copy import deepcopy
from datetime import datetime

from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import SurveyResponseDocument, DataRecordDocument
from mangrove.datastore.entity import DataRecord
from mangrove.utils.types import is_string, sequence_to_str, is_sequence, is_empty
from mangrove.utils.dates import utcnow

WEB = u"web"
SMS = u"sms"
SMART_PHONE = u"smartPhone"
TEST_USER = u"test"
#todo: put it in utils and use it while returning SurveyResponse values itself
def convert_dict_keys_to_lowercase(dictionary):
    for key in dictionary.keys():
        dictionary[key.lower()] = dictionary.pop(key)
    return dictionary


def get_survey_responses_by_form_model_id(dbm, form_model_id, batch_size=1000, skip=0):
        start_key = [form_model_id] if form_model_id else []
        end_key = [form_model_id, {}] if form_model_id else [{}, {}]
        return dbm.database.iterview("surveyresponse/surveyresponse", batch_size, reduce=False, include_docs=False, startkey=start_key, endkey=end_key, skip=skip)


def get_survey_response_by_report_view_name(dbm, report_view_name, keys):
    options = {'reduce': False, 'include_docs': True}
    if keys:
        options['keys'] = keys
    return dbm.database.view(report_view_name + "/" + report_view_name, **options)


def reduce_survey_response_by_report_view_name(dbm, report_view_name, keys):
    options = {'reduce': True, 'include_docs': False, 'group': True}
    if keys:
        options['keys'] = keys
    return dbm.database.view(report_view_name + "/" + report_view_name, **options)


class SurveyResponse(DataObject):
    __document_class__ = SurveyResponseDocument

    def __init__(self, dbm, transport_info=None, form_model_id=None, form_model_revision=None, values=None, owner_uid=None,
                 admin_id=None, response=None):
        DataObject.__init__(self, dbm)
        self.response = response
        if transport_info is not None:
            doc = SurveyResponseDocument(channel=transport_info.transport,
                                         destination=transport_info.destination,
                                         form_model_id=form_model_id,
                                         form_model_revision=form_model_revision,
                                         values=values, status=False,
                                         error_message="", owner_uid=owner_uid, modified_by_id=admin_id)

            DataObject._set_document(self, doc)

    @property
    def version(self):
        return self._doc.rev

    @property
    def data_record(self):
        return DataRecord.get(self._dbm, self._doc.data_record_id) if self._doc.data_record_id is not None else None

    @property
    def data_record_id(self):
        return self._doc.data_record_id

    @property
    def destination(self):
        return self._doc.destination

    @property
    def owner_uid(self):
        return self._doc.owner_uid

    @owner_uid.setter
    def owner_uid(self, owner_uid):
        self._doc.owner_uid = owner_uid

    @property
    def modified_by(self):
        return self._doc.modified_by

    @modified_by.setter
    def modified_by(self, modified_by):
        self._doc.modified_by = modified_by

    @property
    def created_by(self):
        return self._doc.created_by

    @created_by.setter
    def created_by(self, created_by):
        self._doc.created_by = created_by

    @property
    def uuid(self):
        return self.id

    @property
    def status(self):
        return self._doc.status

    @property
    def channel(self):
        return self._doc.channel

    @channel.setter
    def channel(self, channel):
        self._doc.channel = channel

    @property
    def form_model_id(self):
        return self._doc.form_model_id

    @property
    def form_model_revision(self):
        return self._doc.form_model_revision

    @form_model_revision.setter
    def form_model_revision(self, form_model_revision):
        self._doc.form_model_revision = form_model_revision

    @form_model_id.setter
    def form_model_id(self, form_model_id):
        self._doc.form_model_id = form_model_id

    @property
    def values(self):
        return self._doc.values

    @property
    def errors(self):
        return self._doc.error_message

    @property
    def event_time(self):
        return self._doc.event_time

    @property
    def submitted_on(self):
        return self._doc.submitted_on

    @property
    def modified(self):
        return self._doc.modified

    def set_form(self, form_model):
        self._doc.form_model_revision = form_model.revision

    def set_answers(self, values):
        if values:
            self._doc.values = values

    def set_status(self, errors):
        if errors.__len__() == 0 and self.response is None:
            self._doc.status = True
            self._doc.error_message = ''
        else:
            self._doc.status = False
            self._doc.error_message = self._to_string(errors)

    def _void_existing_data_record(self, void=True):
        data_record_id = self._doc.data_record_id
        if data_record_id is not None:
            data_record = DataRecord.get(self._dbm, data_record_id)
            data_record.void(void)
            self._doc.data_record_history.append(data_record_id)

    def create(self, data_record_id):
        self._doc.data_record_id = data_record_id
        self.save()

    def update(self, bound_form_model, data, entity=None):
        assert self.errors == ''
        submission_information = dict(form_code=bound_form_model.form_code)
        data_record_id = self.add_data(data=data,
                                       submission=submission_information)
        self._void_existing_data_record()
        self._doc.data_record_id = data_record_id
        self.save()

    def void(self, void=True):
        self._void_existing_data_record(void)
        super(SurveyResponse, self).void(void)

    def add_data(self, entity=None, data=(), event_time=None, submission=None, multiple_records=False):
        """
        Add a new datarecord to this Entity and return a UUID for the datarecord.
        Arguments:
            data: a sequence of ordered tuples, (label, value, type)
            event_time: the time at which the event occured rather than
                when it was reported
            submission_id: an id to a 'submission' document in the
                submission log from which this data came
        """
        assert is_sequence(data)
        assert event_time is None or isinstance(event_time, datetime)
        assert self.id is not None, u"id should never be none, even if haven't been saved,an entity should have a UUID."
        if event_time is None:
            event_time = utcnow()
        for (label, value) in data:
            if is_empty(label):
                raise ValueError(u'Empty label')
        if multiple_records:
            data_list = []
            for (label, value) in data:
                data_record = DataRecordDocument(
                    event_time=event_time,
                    data=[(label, value)],
                    submission=submission
                )
                data_list.append(data_record)
            return self._dbm._save_documents(data_list)
        else:
            data_record_doc = DataRecordDocument(
                event_time=event_time,
                data=data,
                submission=submission
            )
            return self._dbm._save_document(data_record_doc)

    def _to_string(self, errors):
        if is_string(errors):
            return errors
        if isinstance(errors, dict):
            return sequence_to_str(errors.values())
        if is_sequence(errors):
            return sequence_to_str(errors)
        return None

    def differs_from(self, older_response):
        difference = SurveyResponseDifference(older_response.submitted_on, self.status != older_response.status)
        older_response_values = convert_dict_keys_to_lowercase(older_response.values)
        new_response_values = convert_dict_keys_to_lowercase(self.values)

        for key in new_response_values.keys():
            if key in older_response_values.keys():
                if new_response_values[key] != older_response_values[key]:
                    difference.add(key, older_response_values[key], new_response_values[key])
            else:
                difference.add(key, '', new_response_values[key])
        return difference

    def copy(self):
        survey_copy = SurveyResponse(None)
        survey_copy._doc = SurveyResponseDocument(self._doc.channel, self._doc.destination,
                                                  deepcopy(self.values), self.id, self.status, self.errors,
                                                  self.form_model_id, self.form_model_revision,
                                                  self.data_record.id if self.data_record else None,
                                                  deepcopy(self.event_time))
        return survey_copy

    @property
    def is_anonymous_submission(self):
        return self._doc.is_anonymous_submission

    @is_anonymous_submission.setter
    def is_anonymous_submission(self, value):
        self._doc.is_anonymous_submission = value

class SurveyResponseDifference(object):
    def __init__(self, submitted_on, status_changed):
        self.created = submitted_on
        self.status_changed = status_changed
        self.changed_answers = {}

    def add(self, key, old_value, new_value):
        self.changed_answers[key] = {'old': old_value, 'new': new_value}

    def __eq__(self, other):
        assert isinstance(other, SurveyResponseDifference)
        if self.created == other.created and self.status_changed == other.status_changed and self.changed_answers == other.changed_answers:
            return True
