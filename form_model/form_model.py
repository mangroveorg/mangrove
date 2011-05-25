# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from mangrove.datastore.database import DatabaseManager, DataObject
from mangrove.datastore import datadict
from mangrove.datastore.documents import FormModelDocument
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, QuestionCodeAlreadyExistsException, EntityQuestionAlreadyExistsException, MangroveException, DataObjectAlreadyExists, EntityQuestionCodeNotSubmitted
from mangrove.form_model.field import TextField, field_attributes
from mangrove.utils.types import is_sequence, is_string, is_empty, is_not_empty
from mangrove.form_model import field


def get_form_model_by_code(dbm, code):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(code)
    rows = dbm.load_all_rows_in_view('questionnaire', key=code)
    if not len(rows):
        raise FormModelDoesNotExistsException(code)

    # todo: this is screwy! This two types of forms, reg and otherwise, look like a bad idea...
    doc = dbm._load_document(rows[0]['value']['_id'], FormModelDocument)
    if doc.type == 'registration':
        form = RegistrationFormModel.new_from_db(dbm, doc)
    else:
        form = FormModel.new_from_db(dbm, doc)
    return form


class FormModel(DataObject):
    __document_class__ = FormModelDocument

    def __init__(self, dbm, name=None, label=None, form_code=None, fields=None, entity_type=None, type=None,
                 language="eng"):
        assert isinstance(dbm, DatabaseManager)
        assert name is None or is_not_empty(name)
        assert fields is None or is_sequence(fields)
        assert form_code is None or (is_string(form_code) and is_not_empty(form_code))
        assert type is None or is_not_empty(type)

        DataObject.__init__(self, dbm)

        self.form_fields = []
        self.errors = []
        self.answers = {}

        # Are we being constructed from scratch or existing doc?
        if name is None:
            return

        # Not made from existing doc, so build ourselves up
        self.form_fields = fields
        self.validate_fields()

        doc = FormModelDocument()
        doc.name = name
        doc.add_label(language, label)
        doc.form_code = form_code
        doc.entity_type = entity_type
        doc.type = type
        doc.active_languages = language
        self._set_document(doc)

    def _set_document(self, document):
        DataObject._set_document(self, document)

        # make form_model level fields for any json fields in to
        for json_field in document.json_fields:
            f = field.create_question_from(json_field, self._dbm)
            self.form_fields.append(f)


    def _check_if_form_code_is_unique(self, value):
        try:
            get_form_model_by_code(self._dbm, value)
            raise DataObjectAlreadyExists('Form Model', 'Form Code', value)
        except FormModelDoesNotExistsException:
            pass

    def save(self):
        # convert fields to json fields before save
        if self._doc.rev is None:
            self._check_if_form_code_is_unique(self.form_code)
        self._doc.json_fields = [f._to_json() for f in self.form_fields]
        return DataObject.save(self)

    def validate(self):
        self.validate_fields()
        return True

    def validate_fields(self):
        self.validate_existence_of_only_one_entity_field()
        self.validate_uniqueness_of_field_codes()
        return True

    def get_field_by_name(self, name):
        for field in self.form_fields:
            if field.name == name:
                return field
        return None

    def validate_uniqueness_of_field_codes(self):
        """ Validate all question codes are unique
        """
        code_list = [f.question_code for f in self.form_fields]
        code_list_without_duplicates = list(set(code_list))
        if len(code_list) != len(code_list_without_duplicates):
            raise QuestionCodeAlreadyExistsException("All question codes must be unique")

    def validate_existence_of_only_one_entity_field(self):
        """Validate only 1 entity question is there"""
        entity_question_list = [f for f in self.form_fields if isinstance(f, TextField) and f.is_entity_field == True]
        if len(entity_question_list) > 1:
            raise EntityQuestionAlreadyExistsException("Entity Question already exists")

    def add_field(self, field):
        self.form_fields.append(field)
        self.validate_fields()
        return self.form_fields

    def delete_field(self, question_code):
        self.form_fields = [f for f in self.form_fields if f.question_code != question_code]
        self.validate_fields()

    def delete_all_fields(self):
        self.form_fields = []

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
        for field in self.form_fields:
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
        eq = None
        for f in self.form_fields:
            if isinstance(f, TextField) and f.is_entity_field:
                eq = f
                break
        return eq

    @property
    def form_code(self):
        return self._doc.form_code

    @form_code.setter
    def form_code(self, value):
        if value != self._doc.form_code:
            self._check_if_form_code_is_unique(value)
        self._doc.form_code = value

    @property
    def fields(self):
        return self.form_fields

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
    __document_class__ = FormModelDocument

    def __init__(self, dbm, name=None, form_code=None, fields=None, entity_type=None,
                 language="eng"):
        FormModel.__init__(self, dbm, name=name, label=None, form_code=form_code, fields=fields, entity_type=entity_type
                           , type='registration',
                           language=language)

    def validate_existence_of_only_one_entity_type_field(self):
        """Validate only 1 entity type question is there
        """
        ets = [f for f in self.form_fields if isinstance(f, TextField) and f.question_code.lower() == 't']
        if len(ets) > 1:
            raise EntityQuestionAlreadyExistsException("Entity Type Question already exists")

    def validate_fields(self):
        self.validate_existence_of_only_one_entity_type_field()
        self.validate_uniqueness_of_field_codes()
        return True

    @property
    def location(self):
        location_string = self.answers.get('location')
        if location_string is None:
            return location_string
        location_list = location_string.split(",")
        return [x for x in location_list if x != "" and x != " "]

    #    TODO: Implement these
    @property
    def aggregation_paths(self):
        return None


class FormSubmission(object):
    def _to_three_tuple(self):
        return [(field, value, self.form_model.get_field_by_name(field).ddtype)  for (field, value) in
                self.cleaned_data.items()]

    def __init__(self, form_model, form_answers):
        self.form_model = form_model
        self.form_answers = form_answers
        entity_question = self.form_model.entity_question
        self.short_code = self.form_answers.get(entity_question.question_code)
        if self.short_code is not None:
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
        if self.short_code is None or self.short_code == "":
            raise EntityQuestionCodeNotSubmitted()
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
