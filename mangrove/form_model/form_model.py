# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from collections import OrderedDict
from mangrove.form_model.location import Location
from mangrove.form_model.validator_factory import validator_factory
from mangrove.datastore import entity
from mangrove.datastore.database import DatabaseManager, DataObject
from mangrove.datastore.documents import FormModelDocument, attributes
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, QuestionCodeAlreadyExistsException,\
    EntityQuestionAlreadyExistsException, MangroveException, DataObjectAlreadyExists, QuestionAlreadyExistsException
from mangrove.form_model.field import TextField, create_question_from
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
REPORTER = "reporter"
GLOBAL_REGISTRATION_FORM_ENTITY_TYPE = "registration"



def get_form_model_by_code(dbm, code):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(code)
    rows = dbm.load_all_rows_in_view('questionnaire', key=code)
    if not len(rows):
        raise FormModelDoesNotExistsException(code)

    doc = FormModelDocument.wrap(rows[0]['value'])
    return FormModel.new_from_doc(dbm, doc)

def list_form_models_by_code(dbm, codes):
    assert isinstance(dbm, DatabaseManager)
    assert is_sequence(codes)

    rows = dbm.load_all_rows_in_view('questionnaire', keys=codes)

    def _row_to_form_model(row):
        doc = FormModelDocument.wrap(row['value'])
        return FormModel.new_from_doc(dbm, doc)

    return map(_row_to_form_model, rows)

def get_form_model_by_entity_type(dbm, entity_type):
    assert isinstance(dbm, DatabaseManager)
    assert is_sequence(entity_type)
    rows = dbm.view.registration_form_model_by_entity_type(key=entity_type, include_docs=True)
    if len(rows):
        doc = FormModelDocument.wrap(rows[0]['doc'])
        return FormModel.new_from_doc(dbm, doc)
    return None


class FormModel(DataObject):
    __document_class__ = FormModelDocument

    @classmethod
    def new_from_doc(cls, dbm, doc):
        return super(FormModel, cls).new_from_doc(dbm, doc)

    def __init__(self, dbm, name=None, label=None, form_code=None, fields=None, entity_type=None, type=None,
                 language="en", is_registration_model=False, state=attributes.ACTIVE_STATE, validators=None, enforce_unique_labels = True):
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
        doc.state = state
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
        return  self._case_insensitive_lookup(values, self.entity_question.code)

    def get_entity_type(self, values):
        entity_type = self._case_insensitive_lookup(values, ENTITY_TYPE_FIELD_CODE)
        return entity_type.lower() if is_not_empty(entity_type) else None

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

    def is_registration_form(self):
        return self._doc['is_registration_model']

    def entity_defaults_to_reporter(self):
        return self.entity_type == [REPORTER]

    def is_inactive(self):
        return True if self._doc.state.lower() == attributes.INACTIVE_STATE.lower() else False

    def is_active(self):
        return True if self._doc.state.lower() == attributes.ACTIVE_STATE.lower() else False

    def is_in_test_mode(self):
        return True if self._doc.state.lower() == attributes.TEST_STATE.lower() else False

    def deactivate(self):
        self._doc.state = attributes.INACTIVE_STATE

    def activate(self):
        self._doc.state = attributes.ACTIVE_STATE

    def set_test_mode(self):
        self._doc.state = attributes.TEST_STATE

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
        except MangroveException as e:
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
            return  is_form_code_same_as_existing_form_code
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

    def validate_submission(self, values):
        assert values is not None
        cleaned_values = OrderedDict()
        errors = OrderedDict()
        for validator in self.validators:
            errors.update(validator.validate(values, self.fields, self._dbm))
        values = self._remove_empty_values(values)
        values = self._remove_unknown_fields(values)
        for index, key in enumerate(values):
            field = self._get_field_by_code(key)
            is_valid, result = self._validate_answer_for_field(values[key], field)
            if is_valid:
                cleaned_values[field.code] = result
            else:
                errors["q%s" % str(index + 1)] = result
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
            dict[field.code] = field._to_str()

        return dict


class FormSubmission(object):
    def __init__(self, form_model, form_answers, errors=None, location_tree=None):
        assert errors is None or type(errors) == OrderedDict
        assert form_answers is not None and type(form_answers) == OrderedDict
        assert form_model is not None

        self.form_model = form_model
        self._cleaned_data = form_answers
        entity_short_code = self.get_answer_for(form_model.entity_question.code)
        self.short_code = entity_short_code.lower() if entity_short_code is not None else None
        self.entity_type = self.get_entity_type(form_model)
        self.is_valid = (errors is None or len(errors) == 0)
        self.errors = errors
        self.data_record_id = None
        self.location_tree = location_tree

    @property
    def cleaned_data(self):
        return self._cleaned_data

    @property
    def form_code(self):
        return self.form_model.form_code

    @property
    def saved(self):
        return self.data_record_id is not None

    @property
    def is_registration(self):
        return self.form_model.is_registration_form()

    def save_new(self, dbm):
        entity = self.create_entity(dbm)
        return self._save_data(entity)

    def save(self, dbm):
        return self.save_new(dbm)

    def update(self, dbm):
        return self._save_data(self.get_entity(dbm))

    def _contains_geo_code(self, item):
        item_ = item[0]
        return item_ == GEO_CODE_FIELD_NAME

    def _get_event_time_value(self):
        return self.cleaned_data.get(self._get_event_time_code())

    def _get_event_time_code(self):
        event_time_field = self.form_model.event_time_question
        return event_time_field.code if event_time_field else None

    def _save_data(self, entity):
        submission_information = dict(form_code=self.form_code)
        self.data_record_id = entity.add_data(data=self._values, event_time=self._get_event_time_value(),
            submission=submission_information)
        return self.data_record_id

    def _to_three_tuple(self):
        return [(self.form_model._get_field_by_code(code).name, value, self.form_model._get_field_by_code(code).ddtype)
        for (code, value) in
        (self.cleaned_data.items())]

    def get_answer_for(self, code):
        for key in self._cleaned_data:
            if key.lower() == code.lower():
                return self._cleaned_data[key]
        return None

    @property
    def _values(self):
        return self._to_three_tuple()

    def create_entity(self, dbm):
        location_hierarchy, processed_geometry = Location(self.location_tree, self.form_model).process_entity_creation(
            self.cleaned_data)

        return entity.create_entity(dbm=dbm, entity_type=self.entity_type,
            location=location_hierarchy,
            short_code=self.short_code,
            geometry=processed_geometry)

    def get_entity(self, dbm):
        return entity.get_by_short_code(dbm=dbm, short_code=self.short_code, entity_type=self.entity_type)

    def _get_field_code_by_name(self, field_name):
        field = self.form_model.get_field_by_name(name=field_name)
        return field.code if field is not None else None

    def get_location_field_code(self):
        return self._get_field_code_by_name(LOCATION_TYPE_FIELD_NAME)

    def get_geo_field_code(self):
        return self._get_field_code_by_name(GEO_CODE_FIELD_NAME)

    def get_entity_type(self, form_model):
        entity_type = self.form_model.entity_type
        return [e_type.lower() for e_type in entity_type] if is_not_empty(entity_type) else None


class DataFormSubmission(FormSubmission):
    def __init__(self, form_model, answers, errors):
        super(DataFormSubmission, self).__init__(form_model, answers, errors)

    def create_entity(self, dbm):
        return entity.get_by_short_code(dbm, self.short_code, self.entity_type)


class GlobalRegistrationFormSubmission(FormSubmission):
    def __init__(self, form_model, answers, errors, location_tree=None):
        super(GlobalRegistrationFormSubmission, self).__init__(form_model, answers, errors, location_tree=location_tree)

    def update_location_and_geo_code(self, dbm):
        existing_entity = self.get_entity(dbm)
        location_hierarchy, processed_geometry = Location(self.location_tree, self.form_model).process_entity_creation(
            self.cleaned_data)
        existing_entity.set_location_and_geo_code(location_hierarchy, processed_geometry)
        existing_entity.save()
        values = self._values
        if is_empty(filter(self._contains_geo_code, values)):
            self._cleaned_data[GEO_CODE] = processed_geometry['coordinates'] if processed_geometry is not None else None


    def get_entity_type(self, form_model):
        entity_type = self.get_answer_for(ENTITY_TYPE_FIELD_CODE)
        return [e_type.lower() for e_type in entity_type] if is_not_empty(entity_type) else None

    def void_existing_data_records(self, dbm, form_code=None):
        data_records = dbm.view.data_record_by_form_code(key = [REGISTRATION_FORM_CODE, self.short_code])
        for data_record in data_records:
            data_record_doc = data_record.value
            data_record_doc['void'] = True
            dbm.database.save(data_record_doc)

class EntityRegistrationFormSubmission(FormSubmission):
    def __init__(self, form_model, answers, errors, location_tree=None):
        super(EntityRegistrationFormSubmission, self).__init__(form_model, answers, errors, location_tree=location_tree)

    def get_entity(self, dbm):
        location_hierarchy, processed_geometry = Location(self.location_tree, self.form_model).process_entity_creation(
            self.cleaned_data)
        existing_entity = entity.get_by_short_code(dbm=dbm, short_code=self.short_code, entity_type=self.entity_type)
        existing_entity.set_location_and_geo_code(location_hierarchy, processed_geometry)
        existing_entity.save()
        return existing_entity

    def void_existing_data_records(self, dbm,form_code):
        data_records = dbm.view.data_record_by_form_code(key = [form_code, self.short_code])
        for data_record in data_records:
            data_record_doc = data_record.value
            data_record_doc['void'] = True
            dbm.database.save(data_record_doc)


class FormSubmissionFactory(object):
    def _is_global_registration_form(self, form_model):
        return GLOBAL_REGISTRATION_FORM_ENTITY_TYPE in form_model.entity_type

    def get_form_submission(self, form_model, answers, errors=None, location_tree=None):
        if not form_model.is_registration_form():
            return DataFormSubmission(form_model, answers, errors)
        return GlobalRegistrationFormSubmission(form_model, answers, errors,
            location_tree=location_tree) if self._is_global_registration_form(
            form_model) else EntityRegistrationFormSubmission(form_model, answers, errors, location_tree=location_tree)
