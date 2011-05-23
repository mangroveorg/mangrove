# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from django.contrib.messages.api import success

from mangrove.datastore.database import DatabaseManager, DataObject
from mangrove.datastore import datadict
from mangrove.datastore.datadict import get_or_create_data_dict
from mangrove.datastore.documents import FormModelDocument
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, QuestionCodeAlreadyExistsException, EntityQuestionAlreadyExistsException, MangroveException, DataObjectAlreadyExists, EntityQuestionCodeNotSubmitted, EntityTypeCodeNotSubmitted
from mangrove.form_model.field import TextField, field_attributes
from mangrove.utils.types import is_sequence, is_string, is_empty, is_not_empty
from mangrove.form_model import field

REGISTRATION_FORM_CODE = "REG"
ENTITY_TYPE_FIELD_CODE = "T"
ENTITY_TYPE_FIELD_NAME = "entity_type"
LOCATION_TYPE_FIELD_NAME = "location"


def get_form_model_by_code(dbm, code):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(code)
    rows = dbm.load_all_rows_in_view('mangrove_views/questionnaire', key=code)
    if not len(rows):
        raise FormModelDoesNotExistsException(code)

    doc = dbm._load_document(rows[0]['value']['_id'], FormModelDocument)
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

        self._form_fields = []
        self.errors = []

        # Are we being constructed from scratch or existing doc?
        if name is None:
            return

        # Not made from existing doc, so build ourselves up
        self._form_fields = fields
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
            self._form_fields.append(f)


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
        self._doc.json_fields = [f._to_json() for f in self._form_fields]
        return DataObject.save(self)

    def validate(self):
        self.validate_fields()
        return True

    def validate_fields(self):
        self.validate_existence_of_only_one_entity_field()
        self.validate_uniqueness_of_field_codes()
        return True

    def get_field_by_name(self, name):
        for field in self._form_fields:
            if field.name == name:
                return field
        return None

    def get_field_by_code(self, code):
        for field in self._form_fields:
            if field.code.lower() == code.lower():
                return field
        return None


    def validate_uniqueness_of_field_codes(self):
        """ Validate all question codes are unique
        """
        code_list = [f.code.lower() for f in self._form_fields]
        code_list_without_duplicates = list(set(code_list))
        if len(code_list) != len(code_list_without_duplicates):
            raise QuestionCodeAlreadyExistsException("All question codes must be unique")

    def validate_existence_of_only_one_entity_field(self):
        """Validate only 1 entity question is there"""
        entity_question_list = [f for f in self._form_fields if isinstance(f, TextField) and f.is_entity_field == True]
        if len(entity_question_list) > 1:
            raise EntityQuestionAlreadyExistsException("Entity Question already exists")

    def add_field(self, field):
        self._form_fields.append(field)
        self.validate_fields()
        return self._form_fields

    def delete_field(self, code):
        self._form_fields = [f for f in self._form_fields if f.code != code]
        self.validate_fields()

    def delete_all_fields(self):
        self._form_fields = []

    def add_language(self, language, label=None):
        self._doc.active_languages = language
        if label is not None:
            self._doc.add_label(language, label)

    def _validate_answer_for_field(self, answer, field):
        try:
            value = field.validate(answer)
            return True,value
        except MangroveException as e:
            return False,e.message

    def _find_code(self, answers,code):
        for key in answers:
            if key.lower() == code.lower():
                return answers[key]
        return None

    def _is_valid(self, answers):
        success = True
        cleaned_answers = {}
        errors = {}
        short_code = self._find_code(answers,self.entity_question.code)
        if self._is_registration_form():
            entity_type = self._find_code(answers,ENTITY_TYPE_FIELD_CODE)
            if is_empty(entity_type):
                raise EntityTypeCodeNotSubmitted()
        else:
            if is_empty(short_code):
                raise EntityQuestionCodeNotSubmitted()
        for key in answers:
            field = self.get_field_by_code(key)
            if field is None: continue
            is_valid,result = self._validate_answer_for_field(answers[key], field)
            if is_valid:
                cleaned_answers[field.name] = result
            else:
                success = False
                errors[key] = result
        return success,cleaned_answers,errors

    def validate_submission(self,values):
        success,cleaned_answers,errors = self._is_valid(values)
        short_code = cleaned_answers.get(self.entity_question.name)
        if self._is_registration_form():
            entity_type = cleaned_answers.get(ENTITY_TYPE_FIELD_NAME)
        else:
            entity_type = self.entity_type
        return FormSubmission(self, cleaned_answers,short_code,success,errors,entity_type)

    @property
    def cleaned_data(self):
        return {}

    @property
    def name(self):
        return self._doc.name

    @name.setter
    def name(self, value):
        self._doc.name = value

    @property
    def entity_question(self):
        eq = None
        for f in self._form_fields:
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
        return self._form_fields

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

    def _is_registration_form(self):
        return self.form_code.lower() == REGISTRATION_FORM_CODE.lower()


class FormSubmission(object):
    def _to_three_tuple(self):
        return [(field, value, self.form_model.get_field_by_name(field).ddtype)  for (field, value) in
                self.cleaned_data.items()]

    def __init__(self, form_model, form_answers,short_code,success,errors,entity_type):
        assert errors is None or type(errors) == dict
        assert success is not None and type(success) == bool
        assert form_answers is not None and type(form_answers) == dict
        assert form_model is not None and isinstance(form_model,FormModel)
        
        self.form_model = form_model
        self._cleaned_data = form_answers
        self.short_code = short_code
        self.form_code = self.form_model.form_code
        self.is_valid = success
        self.errors = errors
        self.entity_type = entity_type

    @property
    def values(self):
        return self._to_three_tuple()

    @property
    def cleaned_data(self):
        return self._cleaned_data

def create_default_reg_form_model(manager):
    form_model = _construct_registration_form(manager)
    form_model.save()
    return form_model

def _construct_registration_form(manager):
    location_type = get_or_create_data_dict(manager, name='Location Type', slug='location', primitive_type='location')
    description_type = get_or_create_data_dict(manager, name='description Type', slug='description', primitive_type='string')
    mobile_number_type = get_or_create_data_dict(manager, name='Mobile Number Type', slug='mobile_number', primitive_type='string')
    name_type = get_or_create_data_dict(manager, name='Name', slug='Name', primitive_type='string')
    entity_id_type = get_or_create_data_dict(manager, name='Entity Id Type', slug='entity_id', primitive_type='string')

    #Create registration questionnaire

    question1 = TextField(name=ENTITY_TYPE_FIELD_NAME, code=ENTITY_TYPE_FIELD_CODE, label="What is associated entity type?",
                          language="eng", entity_question_flag=False, ddtype=entity_id_type)

    question2 = TextField(name="name", code="N", label="What is the entity's name?",
                          defaultValue="some default value", language="eng", ddtype=name_type)
    question3 = TextField(name="short_name", code="S", label="What is the entity's short name?",
                          defaultValue="some default value", language="eng", ddtype=name_type,entity_question_flag=True)
    question4 = TextField(name=LOCATION_TYPE_FIELD_NAME, code="L", label="What is the entity's location?",
                          defaultValue="some default value", language="eng", ddtype=location_type)
    question5 = TextField(name="description", code="D", label="Describe the entity",
                          defaultValue="some default value", language="eng", ddtype=description_type)
    question6 = TextField(name="mobile_number", code="M", label="What is the associated mobile number?",
                          defaultValue="some default value", language="eng", ddtype=mobile_number_type)
    form_model = FormModel(manager, name="REG", form_code=REGISTRATION_FORM_CODE, fields=[
                    question1, question2, question3, question4, question5, question6])
    return form_model