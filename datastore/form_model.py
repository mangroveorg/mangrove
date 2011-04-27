# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import uuid
import datarecord
import entity
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import FormModelDocument
from mangrove.datastore.entity import get_entities_by_type
from mangrove.datastore.field import field_attributes
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, EntityQuestionCodeNotSubmitted, FieldDoesNotExistsException
from mangrove.utils.types import is_sequence, is_string

def get(dbm, uuid):
    assert isinstance(dbm, DatabaseManager)
    questionnaire_doc = dbm.load(uuid, FormModelDocument)
    q = FormModel(dbm, _document = questionnaire_doc)
    return q

def get_entity_question(dbm,form_code):
    assert isinstance(dbm, DatabaseManager)
    form_model = _get_questionnaire_by_questionnaire_code(dbm,form_code)
    fields = form_model.fields
    entity_fields=filter(lambda x:x.get(field_attributes.ENTITY_QUESTION_FLAG)== True,fields)
    return entity_fields[0] if len(entity_fields)==1 else None


#TODO : replace entity uuid with short id when we figure out to create the short ids for the entity
#TODO : refactoring to do things python way.
def get_entity_id(dbm,entity_instance_short_id):
    return entity_instance_short_id


def submit(dbm,questionnaire_code,answers,channel):
    assert isinstance(dbm, DatabaseManager)
    questionnaire_document = _get_questionnaire_by_questionnaire_code(dbm, questionnaire_code= questionnaire_code)
    if questionnaire_document is None:
        raise FormModelDoesNotExistsException(questionnaire_code)
    questionnaire = FormModel(dbm, _document= questionnaire_document)

    entity_question = get_entity_question(dbm,questionnaire_code)
    entity_question_code = entity_question.get(field_attributes.FIELD_CODE)
    if answers.get(entity_question_code):
        entity_instance_short_id = answers.pop(entity_question_code)
        entity_instance_id = get_entity_id(dbm,entity_instance_short_id)
    else:
        raise EntityQuestionCodeNotSubmitted()

    for answer in answers:
        question = filter(lambda x:x.get('question_code')==answer,questionnaire.fields)
        if len(question) == 0:
            raise FieldDoesNotExistsException(answer)
        
    if questionnaire.validate():
        if entity_instance_id is not None:
            data_record_id = datarecord.submit(dbm,entity_instance_id,answers,channel)[0]
            return data_record_id
    return None

def _get_questionnaire_by_questionnaire_code(dbm, questionnaire_code):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(questionnaire_code)
    rows = dbm.load_all_rows_in_view('mangrove_views/questionnaire', key=questionnaire_code)
    if len(rows) == 0:
        return None
    questionnaire_id = rows[0]['value']['_id']
    return dbm.load(questionnaire_id, FormModelDocument)

class FormModel(object):

    def __init__(self, dbm, name = None, label = None,form_code = None,fields = None, entity_type_id = None, type=None,language="eng",_document = None):
        '''Construct a new entity.

        Note: _couch_document is used for 'protected' factory methods and
        should not be passed in standard construction.

        If _couch_document is passed, the other args are ignored

        entity_type may be a string (flat type) or sequence (hierarchical type)
        '''
        assert isinstance(dbm, DatabaseManager)
        assert _document is not None or (name and is_sequence(fields) and is_string(form_code) and form_code and is_string(entity_type_id) and entity_type_id and type)
        assert _document is None or isinstance(_document,FormModelDocument)

        self._dbm = dbm

        # Are we being constructed from an existing doc?
        if _document is not None:
            self._doc = _document
            return

        # Not made from existing doc, so create a new one
        self._doc = FormModelDocument()
        self._doc.name=name
        self._doc.add_label(language,label)
        self._doc.form_code=form_code
        self._doc.entity_id=entity_type_id
        self._doc.type=type
        self._doc.active_languages=language
        for question in fields:
            self._doc.fields.append(question._to_json())

    def validate(self):
        return True

    def save(self):
        return self._dbm.save(self._doc).id
    
    def add_question(self,question_to_be_added):
        return self._doc.fields.append(question_to_be_added._to_json())

    def delete_question(self,question_code):
        fields = self._doc.fields
        question_to_be_deleted = filter(lambda x:x[field_attributes.FIELD_CODE] == question_code, fields)[0]
        fields.remove(question_to_be_deleted)

    def delete_all_questions(self):
        self._doc.fields = []

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
    def form_code(self):
        return self._doc.form_code

    @property
    def fields(self):
        return self._doc.fields

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

