# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from mangrove.datastore.database import DatabaseManager, DataObject
from mangrove.datastore import datadict
from mangrove.datastore.documents import FormModelDocument
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, QuestionCodeAlreadyExistsException, EntityQuestionAlreadyExistsException, MangroveException
from mangrove.form_model.field import TextField, field_attributes
from mangrove.utils.types import is_sequence, is_string, is_empty, is_not_empty
from mangrove.form_model import field


def get(dbm, id):
    assert isinstance(dbm, DatabaseManager)
    return dbm.get(id, FormModel)


def get_questionnaire(dbm, questionnaire_code):
    id = _get_questionnaire_id_by_questionnaire_code(dbm, questionnaire_code=questionnaire_code)
    if id is None:
        raise FormModelDoesNotExistsException(questionnaire_code)
    return  get(dbm, id)


def _get_questionnaire_id_by_questionnaire_code(dbm, questionnaire_code):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(questionnaire_code)
    rows = dbm.load_all_rows_in_view('mangrove_views/questionnaire', key=questionnaire_code)
    if not len(rows):
        return None
    return rows[0]['value']['_id']


class FormModel(DataObject):
    __document_class__ = FormModelDocument

    def __init__(self, dbm, name=None, label=None, form_code=None, fields=None, entity_type=None, type=None, language="eng"):
        assert isinstance(dbm, DatabaseManager)
        assert name is None or is_not_empty(name)
        assert fields is None or is_sequence(fields)
        assert form_code is None or (is_string(form_code) and is_not_empty(form_code))
        assert type is None or is_not_empty(type)

        DataObject.__init__(self, dbm)
        
        self.questions = []
        self.errors = []
        self.answers = {}

        # Are we being constructed from scratch or existing doc?
        if name is None:
            return

        # Not made from existing doc, so create a new one
        doc = FormModelDocument()
        doc.name = name
        doc.add_label(language, label)
        doc.form_code = form_code
        doc.entity_type = entity_type
        doc.type = type
        doc.active_languages = language

        self._doc = doc

        # TODO: refactor so that can just call _set_document with the new doc
        for question in fields:
            self.add_field(question)

    def _set_document(self, document):
        DataObject._set_document(self, document)
        for question_field in document.fields:
            question = field.create_question_from(question_field)
            self.questions.append(question)

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
        code_list = [question.question_code for question in self.questions]
        code_list_without_duplicates = list(set(code_list))
        if len(code_list) != len(code_list_without_duplicates):
            raise QuestionCodeAlreadyExistsException("All question codes must be unique")

    def validate_existence_of_only_one_entity_question(self):
        """Validate only 1 entity question is there
        """
        text_questions = [question for question in self.questions if isinstance(question, TextField)]
        entity_question_list = [x for x in text_questions if x.is_entity_field == True]
        if len(entity_question_list) > 1:
            raise EntityQuestionAlreadyExistsException("Entity Question already exists")

    def add_field(self, question_to_be_added):
        self.questions.append(question_to_be_added)
        self._doc.fields.append(question_to_be_added._to_json())
        self.validate_fields()
        return self.fields

    def _find_question(self, question_code):
        matched = [field for field in self._doc.fields if field[field_attributes.FIELD_CODE] == question_code]
        return matched[0] if len(matched) > 0 else None

    def delete_field(self, question_code):
        fields = self._doc.fields
        question_to_be_deleted = self._find_question(question_code)
        fields.remove(question_to_be_deleted)

    def delete_all_fields(self):
        self._doc.fields = []
        self.questions = []

    def add_language(self, language, label=None):
        self._doc.active_languages = language
        if label is not None:
            self._doc.add_label(language, label)

    def _validate_answer_for_field(self, answer, field):
        success = True
        value = None
        try:
            value = field.validate(answer)
            self.answers[field.name] = value
        except MangroveException as e:
            success = False
            self.errors.append(e.message)
        return success

    def is_valid(self, answers):
        success = True
        for field in self.fields:
            answer = answers.get(field.question_code)
            if not is_empty(answer):  # ignore empty answers
                is_valid = self._validate_answer_for_field(answer, field)
                if success is True:
                    success = is_valid
        return success

    @property
    def cleaned_data(self):
        return self.answers

    @property
    def name(self):
        return self._doc.name

    @name.setter
    def name(self, value):
        self._doc.name = value

    @property
    def entity_question(self):
        text_questions = [question for question in self.questions if isinstance(question, TextField)]
        entity_question = [x for x in text_questions if x.is_entity_field == True]
        return entity_question[0]

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
    def entity_type(self):
        return self._doc.entity_type

    @entity_type.setter
    def entity_type(self, value):
        self._doc.entity_type = value

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
    def _to_three_tuple(self):
        return [(field, value, datadict.get_default_datadict_type())  for (field, value) in self.cleaned_data.items()]

    def __init__(self, form_model, form_answers):
        self.form_model = form_model
        self.form_answers = form_answers
        entity_question = self.form_model.entity_question
        self.entity_id = self.form_answers.get(entity_question.question_code)
        if(self.entity_id is not None):
            del form_answers[entity_question.question_code]
        self.form_code = self.form_model.form_code
        self.answers = form_model

    @property
    def values(self):
        return self._to_three_tuple()

    @property
    def cleaned_data(self):
        return self.form_model.cleaned_data

    def is_valid(self):
        return self.form_model.is_valid(self.form_answers)

    def _parse_field(self, form_field, answer):
        if answer is None:
            return None
        if form_field.get("type") == field_attributes.INTEGER_FIELD:
            return int(answer)
        return answer.strip()

    @property
    def errors(self):
        return self.form_model.errors
