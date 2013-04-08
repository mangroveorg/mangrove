from copy import  deepcopy
from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import SurveyResponseDocument
from mangrove.datastore.entity import DataRecord
from mangrove.utils.types import is_string, sequence_to_str, is_sequence

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

    def set_form(self, form_model):
        self._doc.form_model_revision = form_model.revision
        self.entity_question_code = form_model.entity_question.code
        self._doc.test = form_model.is_in_test_mode()

    def set_answers(self, entity_short_code, values):
        if values:
            self._doc.values = values
            self.values[self.entity_question_code] = entity_short_code

    def set_status(self, errors):
        if errors.__len__() == 0:
            self._doc.status = True
        else:
            self._doc.status = False
            self._doc.error_message = self._to_string(errors)

    def _void_existing_data_record(self):
        data_record_id = self._doc.data_record_id
        if data_record_id is not None:
            data_record = DataRecord.get(self._dbm, data_record_id)
            data_record.void()

    def create(self, data_record_id):
        self._doc.data_record_id = data_record_id
        self.save()

    def update(self, data_record_id):
        self._void_existing_data_record()
        self._doc.data_record_id = data_record_id
        self.save()

    def void(self):
        self._void_existing_data_record()
        super(SurveyResponse, self).void()

    def _to_string(self, errors):
        if is_string(errors):
            return errors
        if isinstance(errors, dict):
            return sequence_to_str(errors.values())
        if is_sequence(errors):
            return sequence_to_str(errors)
        return None

    def differs_from(self, older_response):
        difference = SurveyResponseDifference(older_response.created, self.status != older_response.status)
        for key in self.values.keys():
            if key in older_response.values:
                if self.values[key] != older_response.values[key]:
                    difference.add(key, older_response.values[key], self.values[key])
            else:
                difference.add(key,'', self.values[key])
        return difference

    def copy(self):
        survey_copy = SurveyResponse(None)
        survey_copy._doc = SurveyResponseDocument(self._doc.source, self._doc.channel, self._doc.destination,
            deepcopy(self.values), self.id, self.status, self.errors, self.form_code, self.form_model_revision,
            self.data_record.id if self.data_record else None, self.test, deepcopy(self.event_time))
        return survey_copy


class SurveyResponseDifference(object):
    def __init__(self, created, status_changed):
        self.created = created
        self.status_changed = status_changed
        self.changed_answers = {}

    def add(self, key, old_value, new_value):
        self.changed_answers[key] = {'old': old_value, 'new': new_value}

    def __eq__(self, other):
        assert isinstance(other, SurveyResponseDifference)
        if self.created == other.created and self.status_changed == other.status_changed and self.changed_answers == other.changed_answers:
            return True