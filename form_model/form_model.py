# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import FormModelDocument
from mangrove.datastore.field import field_attributes, TextField
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, EntityQuestionAlreadyExistsException, QuestionCodeAlreadyExistsException, EntityQuestionAlreadyExistsException
from mangrove.utils.types import is_sequence, is_string
from mangrove.datastore import field

def get(dbm, uuid):
    assert isinstance(dbm, DatabaseManager)
    questionnaire_doc = dbm.load(uuid, FormModelDocument)
    q = FormModel(dbm, _document=questionnaire_doc)
    return q

def get_questionnaire(dbm, questionnaire_code):
    questionnaire_document = _get_questionnaire_by_questionnaire_code(dbm, questionnaire_code=questionnaire_code)
    if questionnaire_document is None:
        raise FormModelDoesNotExistsException(questionnaire_code)
    questionnaire = FormModel(dbm, _document=questionnaire_document)
    return questionnaire

def _get_questionnaire_by_questionnaire_code(dbm, questionnaire_code):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(questionnaire_code)
    rows = dbm.load_all_rows_in_view('mangrove_views/questionnaire', key=questionnaire_code)
    if not len(rows):
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
        self.questions = []

        # Are we being constructed from an existing doc?
        if _document is not None:
            self._doc = _document
            for question_field in _document.fields:
                question = field.create_question_from(question_field)
                self.questions.append(question)

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
            self.add_field(question)

    def validate(self):
        self.validate_fields()
        return True

    def validate_fields(self):
        self.validate_existence_of_only_one_entity_question()
        self.validate_uniqueness_of_question_codes()
        return True

    def validate_uniqueness_of_question_codes(self):
        """ Validate all question codes are unique
        """
        code_list = [code.question_code for code in self.questions]
        code_list_without_duplicates = list(set(code_list))
        if len(code_list) != len(code_list_without_duplicates):
            raise QuestionCodeAlreadyExistsException("All question codes must be unique")

    def validate_existence_of_only_one_entity_question(self):
        """Validate only 1 entity question is there
        """
        text_questions = [question for question in self.questions if isinstance(question, TextField)]
        entity_question_list= [x for x in text_questions if x.is_entity_field ==True]
        if len(entity_question_list)>1:
            raise EntityQuestionAlreadyExistsException("Entity Question already exists")

    def save(self):
        return self._dbm.save(self._doc).id

    def add_field(self,question_to_be_added):
        self.questions.append(question_to_be_added)
        self._doc.fields.append(question_to_be_added._to_json())
        self.validate_fields()
        return self.fields

    def _find_question(self, question_code):
        matched = [field for field in self._doc.fields if field[field_attributes.FIELD_CODE] == question_code]
        return matched[0] if len(matched) > 0 else None
    
    def delete_field(self,question_code):
        fields = self._doc.fields
        question_to_be_deleted = self._find_question(question_code)
        fields.remove(question_to_be_deleted)

    def delete_all_fields(self):
        self._doc.fields = []
        self.questions = []

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

    @name.setter
    def name(self, value):
        self._doc.name = value

    @property
    def form_code(self):
        return self._doc.form_code

    @form_code.setter
    def form_code(self, value):
        self._doc.form_code = value

    @property
    def fields(self):
        return self.questions

    @property
    def entity_id(self):
        return self._doc.entity_id

    @entity_id.setter
    def entity_id(self, value):
        self._doc.entity_id = value

    @property
    def type(self):
        return self._doc.type

    @property
    def label(self):
        return self._doc.label

    @property
    def activeLanguages(self):
        return self._doc.active_languages

class FormSubmission(object):
    def __init__(self,form_model, answers):
        result = {}
        entity_id = None
        for field_code,answer in answers.items():
            form_field = form_model._find_question(field_code)
            if form_field is None: continue  #Ignore unknown fields
            if form_field.get(field_attributes.ENTITY_QUESTION_FLAG):
                entity_id = self._parse_field(form_field,answer)
            else:
                result[form_field.get(field_attributes.NAME)] = self._parse_field(form_field,answer)
        self.entity_id = entity_id
        self.form_code = form_model.form_code
        self.values = result

    def is_valid(self):
        self.errors = False
        return True

    def _parse_field(self, form_field, answer):
        if form_field.get("type") == field_attributes.INTEGER_FIELD:
            return int(answer)
        else:
            return answer
