# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore import entity
from mangrove.datastore.database import DatabaseManager, DataObject
from mangrove.datastore.datadict import get_or_create_data_dict
from mangrove.datastore.documents import FormModelDocument, attributes
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, QuestionCodeAlreadyExistsException,\
    EntityQuestionAlreadyExistsException, MangroveException, DataObjectAlreadyExists, EntityQuestionCodeNotSubmitted,\
    EntityTypeCodeNotSubmitted, ShortCodeTooLongException, NoQuestionsSubmittedException
from mangrove.form_model.field import TextField, GeoCodeField, HierarchyField
from mangrove.utils.geo_utils import convert_to_geometry
from mangrove.utils.types import is_sequence, is_string, is_empty, is_not_empty
from mangrove.form_model import field

ARPT_SHORT_CODE = "dummy"

REGISTRATION_FORM_CODE = "reg"
ENTITY_TYPE_FIELD_CODE = "t"
ENTITY_TYPE_FIELD_NAME = "entity_type"
LOCATION_TYPE_FIELD_NAME = "location"
LOCATION_TYPE_FIELD_CODE = "l"
GEO_CODE = "g"
GEO_CODE_FIELD = "geo_code"

NAME_FIELD = "name"
NAME_FIELD_CODE = "n"
SHORT_CODE_FIELD = "short_code"
SHORT_CODE = "s"
DESCRIPTION_FIELD = "description"
DESCRIPTION_FIELD_CODE = "d"
MOBILE_NUMBER_FIELD = "mobile_number"
MOBILE_NUMBER_FIELD_CODE = "m"
REPORTER = "reporter"

def get_form_model_by_code(dbm, code):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(code)
    rows = dbm.load_all_rows_in_view('questionnaire', key=code)
    if not len(rows):
        raise FormModelDoesNotExistsException(code)

    doc = dbm._load_document(rows[0]['value']['_id'], FormModelDocument)
    form = FormModel.new_from_doc(dbm, doc)
    return form


class FormModel(DataObject):
    __document_class__ = FormModelDocument

    def __init__(self, dbm, name=None, label=None, form_code=None, fields=None, entity_type=None, type=None,
                 language="eng", state=attributes.ACTIVE_STATE):
        assert isinstance(dbm, DatabaseManager)
        assert name is None or is_not_empty(name)
        assert fields is None or is_sequence(fields)
        assert form_code is None or (is_string(form_code) and is_not_empty(form_code))
        assert type is None or is_not_empty(type)
        assert entity_type is None or is_sequence(entity_type)

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
        doc.state = state
        doc.active_languages = language
        DataObject._set_document(self, doc)

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
            return True, value
        except MangroveException as e:
            return False, e.message

    def _find_code(self, answers, code):
        for key in answers:
            if key.lower() == code.lower():
                return answers[key]
        return None

    def _is_valid(self, answers):
        cleaned_answers = {}
        errors = {}
        short_code = self._find_code(answers, self.entity_question.code)
        if self.is_registration_form():
            entity_code = self._find_code(answers, ENTITY_TYPE_FIELD_CODE)
            if is_empty(entity_code):
                raise EntityTypeCodeNotSubmitted()
            if short_code is not None and len(short_code) > 12:
                raise ShortCodeTooLongException()
        else:
            if is_empty(short_code):
                raise EntityQuestionCodeNotSubmitted()
        for key in answers:
            field = self.get_field_by_code(key)
            if field is None:
                continue
            answer = answers[key]
            if is_empty(answer):
                continue
            is_valid, result = self._validate_answer_for_field(answer, field)
            if is_valid:
                cleaned_answers[field.code] = result
            else:
                errors[key] = result
        return cleaned_answers, errors

    def validate_submission(self, values):
        if values is None or len(values) == 1:
            raise NoQuestionsSubmittedException()
        cleaned_answers, errors = self._is_valid(values)
        return FormSubmission(self, cleaned_answers, errors)

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

    def is_registration_form(self):
        return self.form_code.lower() == REGISTRATION_FORM_CODE.lower()

    def entity_defaults_to_reporter(self):
        return self.entity_type == [REPORTER]

    def is_inactive(self):
        return True if self._doc.state == attributes.INACTIVE_STATE else False

    def is_active(self):
        return True if self._doc.state == attributes.ACTIVE_STATE else False

    def is_in_test_mode(self):
        return True if self._doc.state == attributes.TEST_STATE else False

    def deactivate(self):
        self._doc.state = attributes.INACTIVE_STATE

    def activate(self):
        self._doc.state = attributes.ACTIVE_STATE

    def set_test_mode(self):
        self._doc.state = attributes.TEST_STATE


class FormSubmission(object):
    def _to_three_tuple(self):
        return [(self.form_model.get_field_by_code(field).name, value, self.form_model.get_field_by_code(field).ddtype)
        for (field, value) in
        self.cleaned_data.items()]

    def _get_answer_for(self, code):
        for key in self._cleaned_data:
            if key.lower() == code.lower():
                return self._cleaned_data[key]
        return None

    def __init__(self, form_model, form_answers, errors=None):
        assert errors is None or type(errors) == dict
        assert form_answers is not None and type(form_answers) == dict

        self.form_model = form_model
        self._cleaned_data = form_answers
        short_code = self._get_answer_for(form_model.entity_question.code)
        self.short_code = short_code.lower() if short_code is not None else None
        self.form_code = self.form_model.form_code
        self.is_valid = (errors is None or len(errors) == 0)
        self.errors = errors
        if form_model.is_registration_form():
            entity_type = self._get_answer_for(ENTITY_TYPE_FIELD_CODE)
        else:
            entity_type = self.form_model.entity_type
        type_hierarchy = [e_type.lower() for e_type in entity_type]
        self.entity_type = type_hierarchy

    @property
    def values(self):
        return self._to_three_tuple()

    @property
    def cleaned_data(self):
        return self._cleaned_data

    def to_entity(self, dbm):
        if self.form_model.is_registration_form():
            location = self.cleaned_data.get(LOCATION_TYPE_FIELD_CODE)
            return entity.create_entity(dbm=dbm, entity_type=self.entity_type,
                                        location=location,
                                        short_code=self.short_code,
                                        geometry=convert_to_geometry(self.cleaned_data.get(GEO_CODE)))
        return entity.get_by_short_code(dbm, self.short_code, self.entity_type)


def create_default_reg_form_model(manager):
    form_model = _construct_registration_form(manager)
    form_model.save()
    return form_model


def _construct_registration_form(manager):
    location_type = get_or_create_data_dict(manager, name='Location Type', slug='location', primitive_type='string')
    geo_code_type = get_or_create_data_dict(manager, name='GeoCode Type', slug='geo_code', primitive_type='geocode')
    description_type = get_or_create_data_dict(manager, name='description Type', slug='description',
                                               primitive_type='string')
    mobile_number_type = get_or_create_data_dict(manager, name='Mobile Number Type', slug='mobile_number',
                                                 primitive_type='string')
    name_type = get_or_create_data_dict(manager, name='Name', slug='name', primitive_type='string')
    entity_id_type = get_or_create_data_dict(manager, name='Entity Id Type', slug='entity_id', primitive_type='string')

    #Create registration questionnaire

    question1 = HierarchyField(name=ENTITY_TYPE_FIELD_NAME, code=ENTITY_TYPE_FIELD_CODE,
                               label="What is associated subject type?",
                               language="eng", ddtype=entity_id_type)

    question2 = TextField(name=NAME_FIELD, code=NAME_FIELD_CODE, label="What is the subject's name?",
                          defaultValue="some default value", language="eng", ddtype=name_type)
    question3 = TextField(name=SHORT_CODE_FIELD, code=SHORT_CODE, label="What is the subject's Unique ID Number",
                          defaultValue="some default value", language="eng", ddtype=name_type,
                          entity_question_flag=True)
    question4 = HierarchyField(name=LOCATION_TYPE_FIELD_NAME, code=LOCATION_TYPE_FIELD_CODE,
                               label="What is the subject's location?",
                               language="eng", ddtype=location_type)
    question5 = GeoCodeField(name=GEO_CODE_FIELD, code=GEO_CODE, label="What is the subject's GPS co-ordinates?",
                             language="eng", ddtype=geo_code_type)
    question6 = TextField(name=DESCRIPTION_FIELD, code=DESCRIPTION_FIELD_CODE, label="Describe the subject",
                          defaultValue="some default value", language="eng", ddtype=description_type)
    question7 = TextField(name=MOBILE_NUMBER_FIELD, code=MOBILE_NUMBER_FIELD_CODE,
                          label="What is the mobile number associated with the subject?",
                          defaultValue="some default value", language="eng", ddtype=mobile_number_type)
    form_model = FormModel(manager, name="reg", form_code=REGISTRATION_FORM_CODE, fields=[
        question1, question2, question3, question4, question5, question6, question7], entity_type=["Registration"])
    return form_model