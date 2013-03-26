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

    def void(self, void=True):
        data_record_id = self._doc.data_record_id
        if data_record_id is not None:
            data_record = DataRecord.get(self._dbm, data_record_id)
            data_record.void(void)

        DataObject.void(self, void)

    def get_entity_short_code(self, entity_question_code):
        return self.values[entity_question_code]

    def set_entity(self, entity_question_code, entity_short_code):
        self.values[entity_question_code] = entity_short_code

    def delete(self):
        data_record_id = self._doc.data_record_id
        if data_record_id is not None:
            data_record = DataRecord.get(self._dbm, data_record_id)
            data_record.delete()
        super(SurveyResponse, self).delete()

    def update(self, status, errors, entity_question_code, entity_short_code, data_record_id=None, is_test_mode=False):
        self.set_entity(entity_question_code, entity_short_code)
        self._doc.status = status
        self._doc.data_record_id = data_record_id
        self._doc.error_message = self._to_string(errors)
        self._doc.test = is_test_mode
        self.save()

    def update_form_model_revision(self, form_model_revision):
        self._doc.form_model_revision = form_model_revision
        self.save()

    def _to_string(self, errors):
        if is_string(errors):
            return errors
        if isinstance(errors, dict):
            return sequence_to_str(errors.values())
        if is_sequence(errors):
            return sequence_to_str(errors)
        return None