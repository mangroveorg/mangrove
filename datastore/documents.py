# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from couchdb.mapping import TextField, Document, DateTimeField, DictField, BooleanField, ListField
import datetime
import calendar
from uuid import uuid4
from time import struct_time
from mangrove.utils.types import is_sequence
from ..utils.dates import py_datetime_to_js_datestring, js_datestring_to_py_datetime, utcnow

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
    ACTIVE_LANGUAGES='activeLanguages'

# This class can take care of non-json serializable objects. Another solution is to plug in a custom json encoder/decoder.
class TZAwareDateTimeField(DateTimeField):
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

    def __init__(self, id = None, document_type=None, **values):
        if id is None:
            id = uuid4().hex
        Document.__init__(self,id=id, **values)
        self.created = utcnow()
        self.document_type = document_type
        self.void = False

class EntityDocument(DocumentBase):
    """
        The couch entity document. It abstracts out the couch related functionality and inherits from the Document class of couchdb-python.
        A schema for the entity is enforced here.
    """
    aggregation_paths = DictField()
    
    def __init__(self, id=None, aggregation_paths = None):
        DocumentBase.__init__(self, id = id, document_type = 'Entity')
        self.aggregation_paths = (aggregation_paths if aggregation_paths is not None else {})

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
    # data = RawField()
    data = DictField()
    entity_backing_field = DictField()
    submission_id = TextField()
    event_time =  TZAwareDateTimeField()

    def __init__(self, id = None, entity_doc = None, event_time = None, submission_id = None, data = None):
        assert entity_doc is None or isinstance(entity_doc, EntityDocument)
        DocumentBase.__init__(self, id, 'DataRecord')
        self.submission_id = submission_id
        self.data = data
        self.event_time = event_time
        
        if entity_doc:
            self.entity_backing_field = entity_doc.unwrap()


class SubmissionLogDocument(DocumentBase):
    """
        The submission log document. Will contain metadata about the submission. (Eg: source, submitted_on etc.)
    """
    
    submitted_on = TZAwareDateTimeField()
    source = TextField()

    def __init__(self, source, id=None):
        assert isinstance(source, str)
        DocumentBase.__init__(self, id, 'SubmissionLog')
        self.source = source
        self.submitted_on = utcnow()


class EntityTypeDocument(DocumentBase):
    """
        This document defines the type of the entity.
        """
    name = ListField(TextField())

    def __init__(self,name_=None):
        assert is_sequence(name_)
        DocumentBase.__init__(self, document_type = 'EntityType', id = ".".join([v for v in name_]))
        self.name = name_




        
class FormModelDocument(DocumentBase):
    metadata=DictField()
    name=TextField()
    type=TextField()
    label=DictField()
    form_code=TextField()
    entity_id=TextField()
    fields = ListField(DictField())


    def __init__(self, id=None):
        DocumentBase.__init__(self, id = id, document_type = 'FormModel')
        self.metadata[attributes.ACTIVE_LANGUAGES]=[]

    @property
    def active_languages(self):
        return self.metadata.get(attributes.ACTIVE_LANGUAGES)

    @active_languages.setter
    def active_languages(self,language):
        active_languages = self.metadata[attributes.ACTIVE_LANGUAGES]
        if not filter(lambda x:x==language, active_languages):
            active_languages.append(language)

    def add_label(self,language,label):
        self.label[language]=label

