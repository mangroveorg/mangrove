# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import uuid
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import QuestionnaireDocument
from mangrove.utils.types import is_sequence, is_string

def get(dbm, uuid):
    assert isinstance(dbm, DatabaseManager)
    questionnaire_doc = dbm.load(uuid, QuestionnaireDocument)
    q = Questionnaire(dbm, _document = questionnaire_doc)
    return q

def submit(Questionnaire,answers,channel):
    return True


class Questionnaire(object):

    def __init__(self, dbm, name = None, description = None,short_id = None,questions = None, entity_id = None, _document = None):
        '''Construct a new entity.

        Note: _couch_document is used for 'protected' factory methods and
        should not be passed in standard construction.

        If _couch_document is passed, the other args are ignored

        entity_type may be a string (flat type) or sequence (hierarchical type)
        '''
        assert isinstance(dbm, DatabaseManager)
        assert _document is not None or (name and is_sequence(questions) and is_string(short_id) and short_id and is_string(entity_id) and entity_id)
        assert _document is None or isinstance(_document,QuestionnaireDocument)

        self._dbm = dbm

        # Are we being constructed from an existing doc?
        if _document is not None:
            self._doc = _document
            return

        # Not made from existing doc, so create a new one
        self._doc = QuestionnaireDocument()
        self._doc.name=name
        self._doc.description=description
        self._doc.questions=questions
        self._doc.short_id=short_id
        self._doc.entity_id=entity_id

    def save(self):
        return self._dbm.save(self._doc).id

    @property
    def id(self):
        return self._doc.id

    @property
    def name(self):
        return self._doc.name

    @property
    def short_id(self):
        return self._doc.short_id

    @property
    def questions(self):
        return self._doc.questions

    @property
    def entity_id(self):
        return self._doc.entity_id

    @property
    def type_string(self):
        return self._doc.document_type

    @property
    def description(self):
        return self._doc.description
