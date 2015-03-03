import logging

from couchdb.mapping import TextField, Document, DateTimeField, DictField, BooleanField, ListField, FloatField
import datetime
import calendar
from uuid import uuid1
from time import struct_time
from mangrove.utils.types import is_string
from mangrove.utils.dates import py_datetime_to_js_datestring, js_datestring_to_py_datetime, utcnow


class attributes(object):
    """""Constants for referencing standard attributes in docs."""""
    MODIFIED = 'modified'
    CREATED = 'created'
    EVENT_TIME = 'event_time'
    ENTITY_ID = 'entity_id'
    SUBMISSION_ID = 'submission_id'
    AGG_PATHS = 'aggregation_paths'
    GEO_PATH = '_geo'
    TYPE_PATH = '_type'
    DATA = 'data'
    ACTIVE_LANGUAGES = 'activeLanguages'
    ENABLE_SMS_REPLIES = 'enableSMSReplies'


class TZAwareDateTimeField(DateTimeField):
    """
    Interprets date strings in ISO format with timezones properly.

    """

    def _to_python(self, value):
        if isinstance(value, basestring):
            try:
                value = js_datestring_to_py_datetime(value)
            except ValueError:
                raise ValueError('Invalid ISO date/time %r' % value)
        return value

    def _to_json(self, value):
        if isinstance(value, struct_time):
            value = datetime.datetime.utcfromtimestamp(calendar.timegm(value))
        elif not isinstance(value, datetime.datetime):
            value = datetime.datetime.combine(value, datetime.time(0))
        return py_datetime_to_js_datestring(value)


class DocumentBase(Document):
    created = TZAwareDateTimeField()
    modified = TZAwareDateTimeField()
    document_type = TextField()
    void = BooleanField()

    def __init__(self, id=None, document_type=None, **values):
        if id is None:
            id = uuid1().hex
        Document.__init__(self, id=id, **values)
        self.created = utcnow()
        self.document_type = document_type
        self.void = False

    def post_update(self, dbm, pre_save_object):
        if hasattr(self.__class__, 'registered_functions'):
            for callback in self.__class__.registered_functions:
                try:
                    callback(self, dbm, pre_save_object) if pre_save_object else callback(self, dbm)
                except Exception as e:
                    logging.error(e.message)
                    raise

    @classmethod
    def register_post_update(cls, func):
        if not hasattr(cls, 'registered_functions'):
            cls.registered_functions = []
        cls.registered_functions.append(func)

class EntityDocument(DocumentBase):
    """
    The couch entity document. It abstracts out the couch related functionality and inherits from the Document class
    of couchdb-python.
    A schema for the entity is enforced here.
    """
    aggregation_paths = DictField()
    geometry = DictField()
    centroid = ListField(FloatField())
    gr_id = TextField()
    short_code = TextField()
    data = DictField()

    def __init__(self, id=None, aggregation_paths=None, geometry=None, centroid=None, gr_id=None, short_code=None):
        DocumentBase.__init__(self, id=id, document_type='Entity')
        self.aggregation_paths = (aggregation_paths if aggregation_paths is not None else {})
        self._geometry = geometry
        self._centroid = centroid
        self._gr_id = gr_id
        self.short_code = short_code

    @property
    def entity_type(self):
        if attributes.TYPE_PATH in self.aggregation_paths:
            return self.aggregation_paths[attributes.TYPE_PATH]
        else:
            return None

    @entity_type.setter
    def entity_type(self, typ):
        self.aggregation_paths[attributes.TYPE_PATH] = typ

    @property
    def location(self):
        if attributes.GEO_PATH in self.aggregation_paths:
            return self.aggregation_paths[attributes.GEO_PATH]
        else:
            return None

    @location.setter
    def location(self, loc):
        self.aggregation_paths[attributes.GEO_PATH] = loc

class ContactDocument(DocumentBase):
    """
    The couch entity document. It abstracts out the couch related functionality and inherits from the Document class
    of couchdb-python.
    A schema for the entity is enforced here.
    """
    aggregation_paths = DictField()
    geometry = DictField()
    centroid = ListField(FloatField())
    gr_id = TextField()
    short_code = TextField()
    data = DictField()
    groups = ListField(TextField())

    def __init__(self, id=None, aggregation_paths=None, geometry=None, centroid=None, gr_id=None, short_code=None):
        DocumentBase.__init__(self, id=id, document_type='Contact')
        self.aggregation_paths = (aggregation_paths if aggregation_paths is not None else {})
        self._geometry = geometry
        self._centroid = centroid
        self._gr_id = gr_id
        self.short_code = short_code
        # self.is_data_sender = is_data_sender

    @property
    def entity_type(self):
        if attributes.TYPE_PATH in self.aggregation_paths:
            return self.aggregation_paths[attributes.TYPE_PATH]
        else:
            return None

    @property
    def email(self):
        if self.data.get('email'):
            return self.data['email']['value']
        return None

    @entity_type.setter
    def entity_type(self, typ):
        self.aggregation_paths[attributes.TYPE_PATH] = typ

    @property
    def location(self):
        if attributes.GEO_PATH in self.aggregation_paths:
            return self.aggregation_paths[attributes.GEO_PATH]
        else:
            return None

    @location.setter
    def location(self, loc):
        self.aggregation_paths[attributes.GEO_PATH] = loc

    def add_group(self, group_name):
        self.groups.append(group_name)

class DataRecordDocument(DocumentBase):
    """
    The couch data_record document. It abstracts out the couch related functionality and inherits from the Document
    class of couchdb-python.

    A schema for the data_record is enforced here.
    """
    data = DictField()
    entity = DictField()
    event_time = TZAwareDateTimeField()
    submission = DictField()

    def __init__(self, id=None, entity_doc=None, event_time=None, data=None, submission=None):
        DocumentBase.__init__(self, id, 'DataRecord')
        data_record = {}
        if data is not None:
            for (label, value) in data:
                data_record[label] = {'value': value}
        self.data = data_record
        self.event_time = event_time

        if entity_doc:
            self.entity = entity_doc.unwrap()
        if submission:
            self.submission = submission


class FormModelDocument(DocumentBase):
    metadata = DictField()
    name = TextField()
    # type = TextField()
    label = TextField()
    form_code = TextField()
    is_registration_model = BooleanField(default=False)
    json_fields = ListField(DictField())
    validators = ListField(DictField())
    snapshots = DictField()
    xform = TextField()
    is_media_type_fields_present = BooleanField(default=False)

    def __init__(self, id=None):
        DocumentBase.__init__(self, id=id, document_type='FormModel')
        self.metadata[attributes.ACTIVE_LANGUAGES] = []

    @property
    def active_languages(self):
        return self.metadata[attributes.ACTIVE_LANGUAGES]


    @active_languages.setter
    def active_languages(self, language):
        self.metadata[attributes.ACTIVE_LANGUAGES] = language

    def set_label(self, label):
        self.label = label


class EntityFormModelDocument(FormModelDocument):
    entity_type = ListField(TextField())

    def __init__(self, id=None):
        super(EntityFormModelDocument, self).__init__(id)


class ProjectDocument(FormModelDocument):
    goals = TextField()
    devices = ListField(TextField())
    sender_group = TextField()
    reminder_and_deadline = DictField()
    data_senders = ListField(TextField())
    is_outgoing_sms_replies_enabled = BooleanField()

    def __init__(self, id=None):
        super(ProjectDocument, self).__init__(id)

    @property
    def is_open_survey(self):
        return self.get('is_open_survey', False)

    @is_open_survey.setter
    def is_open_survey(self, value):
        if value:
            self['is_open_survey'] = True
        elif self.is_open_survey:
            del self['is_open_survey']


class SurveyResponseDocument(DocumentBase):
    """
    The processed submission log document. It will contain metadata about the submission. (Eg: source,
    submitted_on etc.)
    along with the parsed key value pairs of the sms that came in
    """

    submitted_on = TZAwareDateTimeField()
    owner_uid = TextField()
    destination = TextField()
    created_by = TextField()
    modified_by = TextField()
    channel = TextField()
    values = DictField()
    status = BooleanField()
    error_message = TextField()
    form_model_id = TextField()
    form_model_revision = TextField()
    data_record_id = TextField()
    event_time = TZAwareDateTimeField()
    data_record_history = ListField(TextField())

    def __init__(self, channel=None, destination=None, values=None, id=None, status=None,
                 error_message=None, form_model_id=None, form_model_revision=None, data_record_id=None,
                 event_time=None, modified_by_id=None, owner_uid=None):
        DocumentBase.__init__(self, id, 'SurveyResponse')
        self.submitted_on = utcnow()
        self.channel = channel
        self.destination = destination
        self.created_by = self.modified_by = modified_by_id
        self.form_model_id = form_model_id
        self.form_model_revision = form_model_revision
        self.values = values
        self.status = status
        self.error_message = error_message
        self.data_record_id = data_record_id
        self.event_time = event_time if event_time is not None else self.created
        self.data_record_history = []
        self.owner_uid = owner_uid

    @property
    def is_anonymous_submission(self):
        return self.get('is_anonymous_submission', False)

    @is_anonymous_submission.setter
    def is_anonymous_submission(self, value):
        if value:
            self['is_anonymous_submission'] = True
        else:
            del self['is_anonymous_submission']


class EnrichedSurveyResponseDocument(DocumentBase):
    """
    The is the event document that will be used for feeds.
    """
    survey_response_modified_time = TZAwareDateTimeField()
    channel = TextField()
    form_code = TextField()
    form_model_revision = TextField()
    values = DictField()
    status = TextField()
    error_message = TextField()
    data_sender = DictField()
    # additional_detail can be empty, for example we will not have the project info when the submission is made via SMS or Xform
    additional_detail = DictField()

    def __init__(self, survey_response_id=None, survey_response_modified_time=None, channel=None, form_code=None,
                 form_model_revision=None, values=None,
                 status=None, error_message=None, data_sender=None, additional_detail=None, void=False):
        DocumentBase.__init__(self, id=survey_response_id, document_type='EnrichedSurveyResponse')
        self.survey_response_modified_time = survey_response_modified_time
        self.channel = channel
        self.form_code = form_code
        self.form_model_revision = form_model_revision
        self.values = values
        self.status = status
        self.error_message = error_message
        self.data_sender = data_sender
        self.additional_detail = additional_detail
        self.void = void

    def update(self, new_document):
        self.survey_response_modified_time = new_document.survey_response_modified_time
        self.form_code = new_document.form_code
        self.form_model_revision = new_document.form_model_revision
        self.values = new_document.values
        self.status = new_document.status
        self.error_message = new_document.error_message
        self.data_sender = new_document.data_sender
        self.additional_detail = new_document.additional_detail
        self.void = new_document.void

    def delete(self):
        self.void = True


class AggregationTreeDocument(DocumentBase):
    root = DictField()
    root_id = TextField()

    def __init__(self, root=None, id=None):
        assert root is None or isinstance(root, dict)

        DocumentBase.__init__(self, id=id, document_type='AggregationTree')

        if root is None:
            self.root = {}


HARD_DELETE = 'hard-delete'
SOFT_DELETE = 'soft-delete'


class EntityActionDocument(DocumentBase):
    """
    Document to represent actions such as unique-id delete

    """
    entity_type = TextField()
    short_code = TextField()
    action = TextField()

    def __init__(self, entity_type, short_code, action):
        DocumentBase.__init__(self, document_type='EntityAction')
        self.entity_type = entity_type
        self.short_code = short_code
        self.action = action

