from copy import deepcopy
from datetime import datetime

from mangrove.datastore.datadict import DataDictType
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


class SurveyResponse(DataObject):
    __document_class__ = SurveyResponseDocument

    def __init__(self, dbm, transport_info=None, form_code=None, form_model_revision=None, values=None, owner_uid=None,
                 admin_id=None):
        DataObject.__init__(self, dbm)
        if transport_info is not None:
            doc = SurveyResponseDocument(channel=transport_info.transport,
                                         destination=transport_info.destination,
                                         form_code=form_code,
                                         form_model_revision=form_model_revision,
                                         values=values, status=False,
                                         error_message="", test=False, owner_uid=owner_uid, modified_by_id=admin_id)

            DataObject._set_document(self, doc)

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

    @channel.setter
    def channel(self, channel):
        self._doc.channel = channel

    @property
    def form_code(self):
        return self._doc.form_code

    @property
    def form_model_revision(self):
        return self._doc.form_model_revision

    @form_model_revision.setter
    def form_model_revision(self, form_model_revision):
        self._doc.form_model_revision = form_model_revision

    @form_code.setter
    def form_code(self, form_code):
        self._doc.form_code = form_code

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
        self.entity_question_code = form_model.entity_question.code
        self._doc.test = form_model.is_in_test_mode()

    def set_answers(self, entity_short_code, values):
        if values:
            self._doc.values = values
            for key in self.values:
                if key.lower() == self.entity_question_code.lower():
                    self.values[key] = entity_short_code
                    return
            self.values[self.entity_question_code] = entity_short_code

    def set_status(self, errors):
        if errors.__len__() == 0:
            self._doc.status = True
            self._doc.error_message = ''
        else:
            self._doc.status = False
            self._doc.error_message = self._to_string(errors)

    def _void_existing_data_record(self):
        data_record_id = self._doc.data_record_id
        if data_record_id is not None:
            data_record = DataRecord.get(self._dbm, data_record_id)
            data_record.void()
            self._doc.data_record_history.append(data_record_id)

    def create(self, data_record_id):
        self._doc.data_record_id = data_record_id
        self.save()

    def update(self, bound_form_model, data, entity):
        assert self.errors == ''
        submission_information = dict(form_code=self.form_code)
        data_record_id = self.add_data(entity, data=data, event_time=bound_form_model._get_event_time_value(),
                                       submission=submission_information)
        self._void_existing_data_record()
        self._doc.data_record_id = data_record_id
        self.save()

    def void(self):
        self._void_existing_data_record()
        super(SurveyResponse, self).void()

    def add_data(self, entity, data=(), event_time=None, submission=None, multiple_records=False):
        """
        Add a new datarecord to this Entity and return a UUID for the datarecord.
        Arguments:
            data: a sequence of ordered tuples, (label, value, type)
                where type is a DataDictType
            event_time: the time at which the event occured rather than
                when it was reported
            submission_id: an id to a 'submission' document in the
                submission log from which this data came
        """
        assert is_sequence(data)
        assert event_time is None or isinstance(event_time, datetime)
        assert self.id is not None, u"id should never be none, even if haven't been saved,an entity should have a UUID."
        # TODO: should we have a flag that says that this has been
        # saved at least once to avoid adding data records for an
        # Entity that may never be saved? Should docs just be saved on
        # init?
        if event_time is None:
            event_time = utcnow()
        for (label, value, dd_type) in data:
            if not isinstance(dd_type, DataDictType) or is_empty(label):
                raise ValueError(u'Data must be of the form (label, value, DataDictType).')
        if multiple_records:
            data_list = []
            for (label, value, dd_type) in data:
                data_record = DataRecordDocument(
                    entity_doc=entity._doc,
                    event_time=event_time,
                    data=[(label, value, dd_type)],
                    submission=submission
                )
                data_list.append(data_record)
            return self._dbm._save_documents(data_list)
        else:
            data_record_doc = DataRecordDocument(
                entity_doc=entity._doc,
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
                                                  self.form_code, self.form_model_revision,
                                                  self.data_record.id if self.data_record else None, self.test,
                                                  deepcopy(self.event_time))
        return survey_copy

    def create_migrated_response(self, status, error_message, void, submitted_on, test, event_time, data_record_id):
        '''This method is only used for migration and should not be used for any functional implementation'''
        self._doc.status = status
        self._doc.error_message = error_message
        self._doc.void = void
        self._doc.submitted_on = submitted_on
        self._doc.test = test
        self._doc.event_time = event_time
        self.create(data_record_id)


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
