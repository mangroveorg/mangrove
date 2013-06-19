# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

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
    ACTIVE_STATE = 'Active'
    INACTIVE_STATE = 'Inactive'
    TEST_STATE = 'Test'


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
        assert entity_doc is None or isinstance(entity_doc, EntityDocument)
        DocumentBase.__init__(self, id, 'DataRecord')
        data_record = {}
        if data is not None:
            for (label, value, dd_type) in data:
                data_record[label] = {'value': value, 'type': dd_type._doc.unwrap()}
        self.data = data_record
        self.event_time = event_time

        if entity_doc:
            self.entity = entity_doc.unwrap()
        if submission:
            self.submission = submission


class DataDictDocument(DocumentBase):
    """""The CouchDB data dictionary document."""""

    primitive_type = TextField()
    constraints = DictField()
    slug = TextField()
    name = TextField()
    description = TextField()
    tags = ListField(TextField())

    def __init__(self, id=None, primitive_type=None, constraints=None, slug=None, name=None,
                 description=None, tags=None, **kwargs):
        """""Create a new CouchDB document that represents a DataDictType"""""
        DocumentBase.__init__(self, id, 'DataDict')

        assert primitive_type is None or is_string(primitive_type)
        assert constraints is None or isinstance(constraints, dict)
        assert slug is None or is_string(slug)
        assert name is None or is_string(name)
        assert description is None or is_string(description)
        assert tags is None or isinstance(tags, list)  # do we want to check that they are strings?
        # how to assert any kwargs?

        self.primitive_type = primitive_type
        if constraints is None:
            self.constraints = {}
        else:
            self.constraints = constraints
        if tags is None:
            self.tags = []
        else:
            self.tags = tags
        self.slug = slug
        self.name = name
        self.description = description
        for arg, value in kwargs.items():
            self[arg] = value


class FormModelDocument(DocumentBase):
    metadata = DictField()
    name = TextField()
    type = TextField()
    label = TextField()
    form_code = TextField()
    state = TextField()
    is_registration_model = BooleanField(default=False)
    entity_type = ListField(TextField())
    json_fields = ListField(DictField())
    validators = ListField(DictField())
    snapshots = DictField()

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


class SubmissionLogDocument(DocumentBase):
    """
    The processed submission log document. It will contain metadata about the submission. (Eg: source,
    submitted_on etc.)
    along with the parsed key value pairs of the sms that came in
    """

    submitted_on = TZAwareDateTimeField()
    source = TextField()
    destination = TextField()
    channel = TextField()
    values = DictField()
    status = BooleanField()
    error_message = TextField()
    form_code = TextField()
    form_model_revision = TextField()
    data_record_id = TextField()
    test = BooleanField()
    event_time = TZAwareDateTimeField()

    def __init__(self, source=None, channel=None, destination=None, values=None, id=None, status=None,
                 error_message=None, form_code=None, form_model_revision=None, data_record_id=None, test=None,
                 event_time=None):
        DocumentBase.__init__(self, id, 'SubmissionLog')
        self.source = source
        self.submitted_on = utcnow()
        self.channel = channel
        self.destination = destination
        self.form_code = form_code
        self.form_model_revision = form_model_revision
        self.values = values
        self.status = status
        self.error_message = error_message
        self.data_record_id = data_record_id
        self.test = test
        self.event_time = event_time if event_time is not None else self.created


class SurveyResponseDocument(DocumentBase):
    """
    The processed submission log document. It will contain metadata about the submission. (Eg: source,
    submitted_on etc.)
    along with the parsed key value pairs of the sms that came in
    """

    submitted_on = TZAwareDateTimeField()
    origin = TextField()
    owner_uid = TextField()
    destination = TextField()
    modified_by = TextField()
    channel = TextField()
    values = DictField()
    status = BooleanField()
    error_message = TextField()
    form_code = TextField()
    form_model_revision = TextField()
    data_record_id = TextField()
    test = BooleanField()
    event_time = TZAwareDateTimeField()
    data_record_history = ListField(TextField())

    def __init__(self, origin=None, channel=None, destination=None, values=None, id=None, status=None,
                 error_message=None, form_code=None, form_model_revision=None, data_record_id=None, test=None,
                 event_time=None,modified_by=None, owner_uid=None):
        DocumentBase.__init__(self, id, 'SurveyResponse')
        self.origin = origin
        self.submitted_on = utcnow()
        self.channel = channel
        self.destination = destination
        self.modified_by = modified_by
        self.form_code = form_code
        self.form_model_revision = form_model_revision
        self.values = values
        self.status = status
        self.error_message = error_message
        self.data_record_id = data_record_id
        self.test = test
        self.event_time = event_time if event_time is not None else self.created
        self.data_record_history = []
        self.owner_uid = owner_uid


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
    #additional_detail can be empty, for example we will not have the project info when the submission is made via SMS or Xform
    additional_detail = DictField()

    def __init__(self, survey_response_id=None, survey_response_modified_time=None, channel=None, form_code=None,
                 form_model_revision=None, values=None,
                 status=None, error_message=None, data_sender=None, additional_detail=None, void=False):
        DocumentBase.__init__(self, id=survey_response_id,document_type='EnrichedSurveyResponse')
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

    def update(self,new_document):
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
