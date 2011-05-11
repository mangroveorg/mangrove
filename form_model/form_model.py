# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from mangrove.datastore.database import DatabaseManager
from mangrove.datastore import datadict
from mangrove.datastore.documents import FormModelDocument
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, QuestionCodeAlreadyExistsException, EntityQuestionAlreadyExistsException, MangroveException
from mangrove.form_model.field import TextField, field_attributes
from mangrove.utils.types import is_sequence, is_string, is_empty, is_not_empty
from mangrove.form_model import field


def get(dbm, uuid):
    assert isinstance(dbm, DatabaseManager)
    questionnaire_doc = dbm.load(uuid, FormModelDocument)
    q = FormModel(dbm, _document=questionnaire_doc)
    return q


def get_questionnaire(dbm, questionnaire_code):
    questionnaire_document = _get_questionnaire_by_questionnaire_code(dbm, questionnaire_code=questionnaire_code)
    if questionnaire_document is None:
        raise FormModelDoesNotExistsException(questionnaire_code)
    if questionnaire_document.type == 'registration':
        questionnaire = RegistrationFormModel(dbm, _document=questionnaire_document)
    else:
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
    def __init__(self, dbm, name=None, label=None, form_code=None, fields=None, entity_type=None, type=None,
                 language="eng", _document=None):
        '''
        Construct a new entity.

        Note: _couch_document is used for 'protected' factory methods and
        should not be passed in standard construction.

        If _couch_document is passed, the other args are ignored

        entity_type may be a string (flat type) or sequence (hierarchical type)

        '''
        assert isinstance(dbm, DatabaseManager)
        assert _document is not None or \
            (name is not None and is_sequence(fields) and is_string(form_code) and
             form_code is not None and type is not None)
        assert _document is None or isinstance(_document, FormModelDocument)

        self._dbm = dbm
        self.questions = []
        self.errors = []
        self.answers = {}
        # Are we being constructed from an existing doc?
        if _document is not None:
            self._doc = _document
            for question_field in _document.fields:
                question = field.create_question_from(question_field)
                self.questions.append(question)

            return

        # Not made from existing doc, so create a new one
        self._doc = FormModelDocument()
        self._doc.name = name
        self._doc.add_label(language, label)
        self._doc.form_code = form_code
        self._doc.entity_type = entity_type
        self._doc.type = type
        self._doc.active_languages = language
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

    def save(self):
        return self._dbm.save(self._doc).id

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
    def id(self):
        return self._doc.id

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


class RegistrationFormModel(FormModel):

    def __init__(self, dbm, name=None, form_code=None, fields=None, entity_type=None,
                 language="eng", _document=None):
        FormModel.__init__(self, dbm, name=name, label=None, form_code=form_code, fields=fields, entity_type=entity_type, type='registration',
                 language=language, _document=_document)

    def validate_existence_of_only_one_entity_type_question(self):
        """Validate only 1 entity type question is there
        """
        text_questions = [question for question in self.questions if isinstance(question, TextField)]
        entity_question_list = [x for x in text_questions if x.question_code.lower() == 'et']
        if len(entity_question_list) > 1:
            raise EntityQuestionAlreadyExistsException("Entity Type Question already exists")

    def validate_fields(self):
        self.validate_existence_of_only_one_entity_type_question()
        self.validate_uniqueness_of_question_codes()
        return True

#    TODO: Implement these
    @property
    def location(self):
        return None

    @property
    def aggregation_paths(self):
        return None


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

class RegistrationFormSubmission(object):

    def _to_three_tuple(self):
        return [(field, value, datadict.get_default_datadict_type())  for (field, value) in self.cleaned_data.items()]

    def __init__(self, form_model, form_answers):
        self.form_model = form_model
        self.form_answers = form_answers
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
