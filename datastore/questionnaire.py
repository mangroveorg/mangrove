# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import uuid
import datarecord
import entity
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import QuestionnaireDocument
from mangrove.datastore.question import question_attributes
from mangrove.utils.types import is_sequence, is_string

def get(dbm, uuid):
    assert isinstance(dbm, DatabaseManager)
    questionnaire_doc = dbm.load(uuid, QuestionnaireDocument)
    q = Questionnaire(dbm, _document = questionnaire_doc)
    return q

#TODO : replace entity uuid with short id when we figure out to create the short ids for the entity
#TODO : refactoring to do things python way.
def submit(dbm,questionnaire_code,entity_uuid,answers,channel):
    assert isinstance(dbm, DatabaseManager)
    questionnaire_document = _get_questionnaire_by_questionnaire_code(dbm, questionnaire_code= questionnaire_code)
    questionnaire = Questionnaire(dbm, _document= questionnaire_document)
    for answer in answers:
        question = filter(lambda x:x.get('sms_code')==answer,questionnaire.questions)
        if question is None:
            return None
    if questionnaire.validate():
        entity_instance = entity.get(dbm, entity_uuid)
        if entity_instance is not None:
            data_record_id = datarecord.submit(dbm,entity_instance.id,answers,channel)[0]
            return data_record_id
    return None

def _get_questionnaire_by_questionnaire_code(dbm, questionnaire_code):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(questionnaire_code)
    rows = dbm.load_all_rows_in_view('mangrove_views/questionnaire', key=questionnaire_code)
    questionnaire_id = rows[0]['value']['_id']
    return dbm.load(questionnaire_id, QuestionnaireDocument)

class Questionnaire(object):

    def __init__(self, dbm, name = None, label = None,questionnaire_code = None,questions = None, entity_id = None, type=None,language="eng",_document = None):
        '''Construct a new entity.

        Note: _couch_document is used for 'protected' factory methods and
        should not be passed in standard construction.

        If _couch_document is passed, the other args are ignored

        entity_type may be a string (flat type) or sequence (hierarchical type)
        '''
        assert isinstance(dbm, DatabaseManager)
        assert _document is not None or (name and is_sequence(questions) and is_string(questionnaire_code) and questionnaire_code and is_string(entity_id) and entity_id and type)
        assert _document is None or isinstance(_document,QuestionnaireDocument)

        self._dbm = dbm

        # Are we being constructed from an existing doc?
        if _document is not None:
            self._doc = _document
            return

        # Not made from existing doc, so create a new one
        self._doc = QuestionnaireDocument()
        self._doc.name=name
        self._doc.add_label(language,label)
        self._doc.questionnaire_code=questionnaire_code
        self._doc.entity_id=entity_id
        self._doc.type=type
        self._doc.active_languages=language
        for question in questions:
            self._doc.questions.append(question._to_json())

    def validate(self):
        return True

    def save(self):
        return self._dbm.save(self._doc).id
    
    def add_question(self,question_to_be_added):
        return self._doc.questions.append(question_to_be_added._to_json())

    def delete_question(self,question_code):
        questions = self._doc.questions
        question_to_be_deleted = filter(lambda x:x[question_attributes.QUESTION_CODE] == question_code, questions)[0]
        questions.remove(question_to_be_deleted)


    def add_language(self, language, label=None):
        self._doc.active_languages = language
        if label is not None:
            self._doc.add_label(language,label)

    @property
    def id(self):
        return self._doc.id

    @property
    def name(self):
        return self._doc.name

    @property
    def questionnaire_code(self):
        return self._doc.questionnaire_code

    @property
    def questions(self):
        return self._doc.questions

    @property
    def entity_id(self):
        return self._doc.entity_id

    @property
    def type(self):
        return self._doc.type

    @property
    def label(self):
        return self._doc.label

    @property
    def activeLanguages(self):
        return self._doc.active_languages

