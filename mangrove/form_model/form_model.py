
from collections import OrderedDict
from datetime import *
from mangrove.datastore.cache_manager import get_cache_manager
from mangrove.form_model.validator_factory import validator_factory
from mangrove.datastore.database import DatabaseManager, DataObject
from mangrove.datastore.documents import FormModelDocument, attributes
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, QuestionCodeAlreadyExistsException, \
    EntityQuestionAlreadyExistsException, DataObjectAlreadyExists, QuestionAlreadyExistsException
from mangrove.form_model.field import TextField
from mangrove.form_model.validators import MandatoryValidator
from mangrove.utils.types import is_sequence, is_string, is_empty, is_not_empty
from mangrove.form_model import field

ARPT_SHORT_CODE = "dummy"

REGISTRATION_FORM_CODE = "reg"
ENTITY_TYPE_FIELD_CODE = "t"
ENTITY_TYPE_FIELD_NAME = "entity_type"

LOCATION_TYPE_FIELD_NAME = "location"
LOCATION_TYPE_FIELD_CODE = "l"
GEO_CODE = "g"
GEO_CODE_FIELD_NAME = "geo_code"

NAME_FIELD = "name"
FORM_CODE = "form_code"
NAME_FIELD_CODE = "n"
SHORT_CODE_FIELD = "short_code"
SHORT_CODE = "s"
DESCRIPTION_FIELD = "description"
DESCRIPTION_FIELD_CODE = "d"
MOBILE_NUMBER_FIELD = "mobile_number"
MOBILE_NUMBER_FIELD_CODE = "m"
EMAIL_FIELD = "email"
EMAIL_FIELD_CODE = "email"
REPORTER = "reporter"
GLOBAL_REGISTRATION_FORM_ENTITY_TYPE = "registration"
FORM_MODEL_EXPIRY_TIME_IN_SEC = 2*60*60

def get_form_model_by_code(dbm, code):
    cache_manger = get_cache_manager()
    key_as_str = get_form_model_cache_key(code, dbm)
    row_value = cache_manger.get(key_as_str)
    if row_value is None:
        row_value = _load_questionnaire(code, dbm)
        cache_manger.set(key_as_str, row_value, time=FORM_MODEL_EXPIRY_TIME_IN_SEC)

    doc = FormModelDocument.wrap(row_value)

    return FormModel.new_from_doc(dbm, doc)
#dummy commit new
def _load_questionnaire(form_code, dbm):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(form_code)
    rows = dbm.load_all_rows_in_view('questionnaire', key=form_code)
    if not len(rows):
        raise FormModelDoesNotExistsException(form_code)
    return rows[0]['value']

def list_form_models_by_code(dbm, codes):
    assert isinstance(dbm, DatabaseManager)
    assert is_sequence(codes)

    rows = dbm.load_all_rows_in_view('questionnaire', keys=codes)

    def _row_to_form_model(row):
        doc = FormModelDocument.wrap(row['value'])
        return FormModel.new_from_doc(dbm, doc)

    return map(_row_to_form_model, rows)

def get_form_model_cache_key(form_code, dbm):
        assert isinstance(dbm, DatabaseManager)
        assert form_code is not None
        return str("%s_%s" % (dbm.database.name, form_code))

def header_fields(form_model, key_attribute="name", ref_header_dict=None):
    header_dict = ref_header_dict or OrderedDict()
    for field in form_model.fields:
        key = field.__getattribute__(key_attribute) if type(key_attribute) == str else key_attribute(field)
        if not header_dict.get(key):
            header_dict.update({key: field.label})
    return header_dict

def get_field_by_attribute_value(form_model, key_attribute,attribute_label):
    #ex: field1.name='first_name' field1.code='q1'
    #    field2.name='location' field2.code='q3'
    #    and both field1 and field2 are form_model fields,
    #    get_field_by_attribute_value(form_model,'name','location') will give back field2
    for field in form_model.fields:
        if field.__getattribute__(key_attribute) == attribute_label:
            return field
    return None

def get_form_model_by_entity_type(dbm, entity_type):
    assert isinstance(dbm, DatabaseManager)
    assert is_sequence(entity_type)
    rows = dbm.view.registration_form_model_by_entity_type(key=entity_type, include_docs=True)
    if len(rows):
        doc = FormModelDocument.wrap(rows[0]['doc'])
        return FormModel.new_from_doc(dbm, doc)
    return None


def get_form_code_by_entity_type(dbm, entity_type):
    form_model = get_form_model_by_entity_type(dbm, entity_type)
    return form_model.form_code if form_model else None

class FormModel(DataObject):
    __document_class__ = FormModelDocument

    @classmethod
    def new_from_doc(cls, dbm, doc):
        return super(FormModel, cls).new_from_doc(dbm, doc)

    def __init__(self, dbm, name=None, label=None, form_code=None, fields=None, entity_type=None, type=None,
                 language="en", is_registration_model=False,  validators=None,
                 enforce_unique_labels=True):
        if not validators: validators = [MandatoryValidator()]
        assert isinstance(dbm, DatabaseManager)
        assert name is None or is_not_empty(name)
        assert fields is None or is_sequence(fields)
        assert form_code is None or (is_string(form_code) and is_not_empty(form_code))
        assert type is None or is_not_empty(type)
        assert entity_type is None or is_sequence(entity_type)

        DataObject.__init__(self, dbm)

        self._snapshots = {}
        self._form_fields = []
        self.errors = []
        self.validators = validators
        self._enforce_unique_labels = enforce_unique_labels
        # Are we being constructed from scratch or existing doc?
        if name is None:
            return

        # Not made from existing doc, so build ourselves up
        self._validate_fields(fields)
        self._form_fields = fields

        doc = FormModelDocument()
        doc.name = name
        doc.set_label(label)
        doc.form_code = form_code
        doc.entity_type = entity_type
        doc.type = type
        doc.active_languages = [language]
        doc.is_registration_model = is_registration_model
        DataObject._set_document(self, doc)

    @property
    def name(self):
        """
        Returns the name of the FormModel
        """
        return self._doc.name

    @name.setter
    def name(self, value):
        """
        Sets the name of the FormModel
        """
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
    def event_time_question(self):
        event_time_questions = [event_time_question for event_time_question in self._form_fields if
                                event_time_question.is_event_time_field]
        return event_time_questions[0] if event_time_questions else None

    def _get_event_time_value(self):
        if self.event_time_question and self.event_time_question.code:
            field = self._get_field_by_code(self.event_time_question.code)
            return datetime.strptime(field.value, field.DATE_DICTIONARY.get(field.date_format)) if field.value else None
        return None

    @property
    def form_code(self):
        return self._doc.form_code

    @form_code.setter
    def form_code(self, value):
        self._doc.form_code = value

    @property
    def fields(self):
        return self._form_fields

    @property
    def choice_fields(self):
        return [field for field in self._form_fields if field.type in ("select", "select1")]

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

    @activeLanguages.setter
    def activeLanguages(self, value):
        self._doc.active_languages = value

    def get_short_code(self, values):
        return self._case_insensitive_lookup(values, self.entity_question.code)

    def get_entity_type(self, values):
        entity_type = self._case_insensitive_lookup(values, ENTITY_TYPE_FIELD_CODE)
        return entity_type.lower() if is_not_empty(entity_type) else None

    def delete(self):
        self._delete_form_model_from_cache()

        super(FormModel, self).delete()

    def _delete_form_model_from_cache(self):
        cache_manger = get_cache_manager()
        cache_key = get_form_model_cache_key(self.form_code, self._dbm)
        cache_manger.delete(cache_key)

    def void(self, void=True):
        self._delete_form_model_from_cache()
        super(FormModel, self).void(void=void)

    def save(self):
        # convert fields and validators to json fields before save
        if not self._is_form_code_unique():
            raise DataObjectAlreadyExists('Form Model', 'Form Code', self.form_code)

        self._doc.json_fields = [f._to_json() for f in self._form_fields]
        self._doc.validators = [validator.to_json() for validator in self.validators]
        json_snapshots = {}
        for key, value in self._snapshots.items():
            json_snapshots[key] = [each._to_json() for each in value]
        self._doc.snapshots = json_snapshots
        self._delete_form_model_from_cache()
        return DataObject.save(self)


    def get_field_by_name(self, name):
        for field in self._form_fields:
            if field.name == name:
                return field
        return None

    def _get_field_by_code(self, code):
        for field in self._form_fields:
            if code is not None and field.code.lower() == code.lower():
                return field
        return None

    def get_field_by_code_and_rev(self, code, revision=None):
        if self.revision == revision or not self._snapshots:
            return self._get_field_by_code(code)

        if revision is None:
            revision = min(self._snapshots, key=lambda x: int(x.split('-')[0]))

        snapshot = self._snapshots.get(revision, [])
        for field in snapshot:
            if field.code.lower() == code.lower(): return field
        return None

    def get_field_code_label_dict(self):
        field_code_label_dict = {}
        for form_field in self._form_fields:
            quoted_label = '&#39;' + form_field.label + '&#39;'
            field_code_label_dict.update({form_field.code:quoted_label})
        return field_code_label_dict

    def _non_rp_fields(self):
        return [field for field in self.fields if not field.is_event_time_field]

    def non_rp_fields_by(self, revision=None):
        if revision is None or revision == self.revision:
            return self._non_rp_fields()
        else:
            return [field for field in self._snapshots.get(revision, []) if not field.is_event_time_field]

    def add_field(self, field):
        self._validate_fields(self._form_fields + [field])
        self._form_fields.append(field)
        return self._form_fields

    def delete_field(self, code):
        self._form_fields = [f for f in self._form_fields if f.code != code]
        self._validate_fields(self._form_fields)

    def delete_all_fields(self):
        self._form_fields = []

    def create_snapshot(self):
        if self._form_fields:
            self._snapshots[self._doc.rev] = self._form_fields

    @property
    def snapshots(self):
        return self._snapshots

    @property
    def revision(self):
        return self._doc.rev

    @property
    def form_fields(self):
        return self._doc["json_fields"]


    def field_names(self):
        return [field['name'] for field in self._doc["json_fields"]]

    def field_codes(self):
        return [field['code'] for field in self._doc["json_fields"]]

    @revision.setter
    def revision(self, rev):
        self._doc.rev = rev

    def is_global_registration_form(self):
        return GLOBAL_REGISTRATION_FORM_ENTITY_TYPE in self.entity_type

    def is_entity_registration_form(self):
        return self._doc['is_registration_model']

    def is_entity_type_reporter(self):
        return self.entity_type == [REPORTER]


    def bind(self, submission):
        self.submission = submission
        for field in self.fields:
            answer = self._case_insensitive_lookup(self.submission, field.code)
            field.set_value(answer)

    def _validate_fields(self, fields):
        self._validate_existence_of_only_one_entity_field(fields)
        self._validate_uniqueness_of_field_codes(fields)
        self._validate_uniqueness_of_field_labels(fields)


    def _validate_uniqueness_of_field_labels(self, fields):
        """ Validate all question labels are unique

        """
        if self._enforce_unique_labels:
            label_list = [f.label.lower() for f in fields]
            label_list_without_duplicates = list(set(label_list))
            if len(label_list) != len(label_list_without_duplicates):
                raise QuestionAlreadyExistsException("All questions must be unique")

    def _validate_uniqueness_of_field_codes(self, fields):
        """ Validate all question codes are unique
        """
        code_list = [f.code.lower() for f in fields]
        code_list_without_duplicates = list(set(code_list))
        if len(code_list) != len(code_list_without_duplicates):
            raise QuestionCodeAlreadyExistsException("All question codes must be unique")

    def _validate_existence_of_only_one_entity_field(self, fields):
        """Validate only 1 entity question is there"""
        entity_question_list = [f for f in fields if isinstance(f, TextField) and f.is_entity_field == True]
        if len(entity_question_list) > 1:
            raise EntityQuestionAlreadyExistsException("Entity Question already exists")

    def _validate_answer_for_field(self, answer, field):
        try:
            value = field.validate(answer)
            return True, value
        except Exception as e:
            field.errors.append(e.message)
            return False, e.message

    def _set_document(self, document):
        DataObject._set_document(self, document)

        # make form_model level fields for any json fields in to
        for json_field in document.json_fields:
            f = field.create_question_from(json_field, self._dbm)
            self._form_fields.append(f)
        for validator_json in document.validators:
            validator = validator_factory(validator_json)
            if validator not in self.validators:
                self.validators.append(validator)

        if hasattr(document, 'snapshots'):
            for key, value in document.snapshots.items():
                self._snapshots[key] = []
                for each in value:
                    f = field.create_question_from(each, self._dbm)
                    self._snapshots[key].append(f)

    def _is_form_code_unique(self):
        try:
            form = get_form_model_by_code(self._dbm, self.form_code)
            is_form_code_same_as_existing_form_code = True if form.id == self.id else False
            return is_form_code_same_as_existing_form_code
        except FormModelDoesNotExistsException:
            return True

    def _find_code(self, answers, code):
        for key in answers:
            if key.lower() == code.lower():
                return answers[key]
        return None

    def _remove_empty_values(self, answers):
        return OrderedDict([(k, v) for k, v in answers.items() if not is_empty(v)])

    def _remove_unknown_fields(self, answers):
        return OrderedDict([(k, v) for k, v in answers.items() if self._get_field_by_code(k) is not None])

    #TODO : does not handle value errors. eg. Text for Number. Done outside the service right now.
    def validate_submission(self, values):
        assert values is not None
        cleaned_values = OrderedDict()
        errors = OrderedDict()
        for validator in self.validators:
            errors.update(validator.validate(values, self.fields, self._dbm))
        values = self._remove_empty_values(values)
        values = self._remove_unknown_fields(values)
        for key in values:
            field = self._get_field_by_code(key)
            index = self.fields.index(field)
            is_valid, result = self._validate_answer_for_field(values[key], field)
            if is_valid:
                cleaned_values[field.code] = result
            else:
                errors[field.code] = result
        return cleaned_values, errors

    def _case_insensitive_lookup(self, values, code):
        for fieldcode in values:
            if fieldcode.lower() == code.lower():
                return values[fieldcode]
        return None

    def stringify(self, values):
        self.bind(values)
        dict = OrderedDict()
        for field in self.fields:
            dict[field.code] = field.convert_to_unicode()

        return dict

    def add_validator(self, validator_class):
        if validator_class not in [validator.__class__ for validator in self.validators]:
            self.validators.append(validator_class())

    def remove_validator(self, validator_class):
        for validator in self.validators:
            if isinstance(validator, validator_class):
                self.validators.remove(validator)
                return