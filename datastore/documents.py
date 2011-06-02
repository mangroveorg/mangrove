# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from couchdb.mapping import TextField, Document, DateTimeField, DictField, BooleanField, ListField, FloatField
import datetime
import calendar
from uuid import uuid1
from time import struct_time
from mangrove.utils.types import is_string
from mangrove.utils.dates import py_datetime_to_js_datestring, js_datestring_to_py_datetime, utcnow


class attributes(object):
    '''Constants for referencing standard attributes in docs.'''
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
    The couch entity document. It abstracts out the couch related functionality and inherits from the Document class of couchdb-python.
    A schema for the entity is enforced here.
    """
    aggregation_paths = DictField()
    geometry = DictField()
    centroid = ListField(FloatField())
    gr_id = TextField()
    short_code = TextField()

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
    submission_id = TextField()
    event_time = TZAwareDateTimeField()
    form_code = TextField()

    def __init__(self, id=None, entity_doc=None, event_time=None, submission_id=None, data=None, form_code = None):
        assert entity_doc is None or isinstance(entity_doc, EntityDocument)
        DocumentBase.__init__(self, id, 'DataRecord')
        self.submission_id = submission_id
        data_record = {}
        if data is not None:
            for (label, value, dd_type) in data:
                data_record[label] = {'value': value, 'type': dd_type._doc.unwrap()}
        self.data = data_record
        self.event_time = event_time

        if entity_doc:
            self.entity = entity_doc.unwrap()
        if form_code:
            self.form_code = form_code


class DataDictDocument(DocumentBase):
    '''The CouchDB data dictionary document.'''

    primitive_type = TextField()
    constraints = DictField()
    slug = TextField()
    name = TextField()
    description = TextField()
    tags = ListField(TextField())

    def __init__(self, id=None, primitive_type=None, constraints=None, slug=None, name=None,
                 description=None, tags=None, **kwargs):
        '''Create a new CouchDB document that represents a DataDictType'''
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


class RawSubmissionLogDocument(DocumentBase):
    """
    The raw submission log document. Will contain metadata about the submission. (Eg: source, submitted_on etc.)
    along with the raw sms string that came in
    """

    submitted_on = TZAwareDateTimeField()
    source = TextField()
    destination = TextField()
    channel = TextField()
    message = TextField()

    def __init__(self, source, channel=None, destination=None, message=None, id=None):
        assert is_string(source)
        DocumentBase.__init__(self, id, 'RawSubmissionLog')
        self.source = source
        self.submitted_on = utcnow()
        self.channel = channel
        self.destination = destination
        self.message = message


class FormModelDocument(DocumentBase):
    metadata = DictField()
    name = TextField()
    type = TextField()
    label = DictField()
    form_code = TextField()
    entity_type = ListField(TextField())
    json_fields = ListField(DictField())

    def __init__(self, id=None):
        DocumentBase.__init__(self, id=id, document_type='FormModel')
        self.metadata[attributes.ACTIVE_LANGUAGES] = []

    @property
    def active_languages(self):
        return self.metadata[attributes.ACTIVE_LANGUAGES]

    @active_languages.setter
    def active_languages(self, language):
        if not language in self.metadata[attributes.ACTIVE_LANGUAGES]:
            self.metadata[attributes.ACTIVE_LANGUAGES].append(language)

    def add_label(self, language, label):
        self.label[language] = label


class SubmissionLogDocument(DocumentBase):
    """
    The processed submission log document. It will contain metadata about the submission. (Eg: source, submitted_on etc.)
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

    def __init__(self, source=None, channel=None, destination=None, values=None, id=None, status=None,
                 error_message=None, form_code=None):
        DocumentBase.__init__(self, id, 'SubmissionLog')
        self.source = source
        self.submitted_on = utcnow()
        self.channel = channel
        self.destination = destination
        self.form_code = form_code
        self.values = values
        self.status = status
        self.error_message = error_message


class AggregationTreeDocument(DocumentBase):
    root = DictField()
    root_id = TextField()

    def __init__(self, root=None, id=None):
        assert root is None or isinstance(root, dict)

        DocumentBase.__init__(self, id=id, document_type='AggregationTree')

        if root is None:
            self.root = {}
