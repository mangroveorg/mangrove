from collections import OrderedDict
import copy
import re
import unicodedata
import xmldict
import xmltodict
import xml.etree.ElementTree as ET
from mangrove.datastore.cache_manager import get_cache_manager
from mangrove.datastore.entity import get_all_entities
from mangrove.form_model.validator_factory import validator_factory
from mangrove.datastore.database import DatabaseManager, DataObject
from mangrove.datastore.documents import FormModelDocument, EntityFormModelDocument
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, QuestionCodeAlreadyExistsException, \
    DataObjectAlreadyExists, QuestionAlreadyExistsException, NoDocumentError
from mangrove.form_model.field import UniqueIdField, ShortCodeField, FieldSet, SelectField, MediaField, UniqueIdUIField
from mangrove.form_model.validators import MandatoryValidator
from mangrove.utils.types import is_sequence, is_string, is_empty, is_not_empty
from mangrove.form_model import field
from xml.sax.saxutils import escape


ARPT_SHORT_CODE = "dummy"

REGISTRATION_FORM_CODE = "reg"
ENTITY_TYPE_FIELD_CODE = "t"
ENTITY_TYPE_FIELD_NAME = "entity_type"

LOCATION_TYPE_FIELD_NAME = "location"
LOCATION_TYPE_FIELD_CODE = "l"
GEO_CODE = "g"
GEO_CODE_FIELD_NAME = "geo_code"

NAME_FIELD = "name"
FORM_MODEL_ID = "form_model_id"
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
FORM_MODEL_EXPIRY_TIME_IN_SEC = 2 * 60 * 60
ENTITY_DELETION_FORM_CODE = "delete"


def get_form_model_by_code(dbm, code):
    cache_manger = get_cache_manager()
    key_as_str = get_form_model_cache_key(code, dbm)
    row_value = cache_manger.get(key_as_str)
    if row_value is None:
        row_value = _load_questionnaire(code, dbm)
        cache_manger.set(key_as_str, row_value, time=FORM_MODEL_EXPIRY_TIME_IN_SEC)

    if row_value.get('is_registration_model') or row_value.get('form_code') == ENTITY_DELETION_FORM_CODE:
        return EntityFormModel.new_from_doc(dbm, EntityFormModelDocument.wrap(row_value))
    return FormModel.new_from_doc(dbm, FormModelDocument.wrap(row_value))


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
    if type(form_code) == unicode:
        return "%s_%s" % (dbm.database.name.encode('utf-8'), form_code.encode('utf-8'))
    return str("%s_%s" % (dbm.database.name, form_code))


def header_fields(form_model, key_attribute="name", ref_header_dict=None):
    header_dict = ref_header_dict or OrderedDict()
    _header_fields(form_model.fields, key_attribute, header_dict)
    return header_dict


def _header_fields(fields, key_attribute, header_dict, parent_field_name=None):
    for field in fields:
        if isinstance(field, FieldSet) and field.is_group():
            _header_fields(field.fields, key_attribute, header_dict, field.code)
            continue
        key = field.__getattribute__(key_attribute) if type(key_attribute) == str else key_attribute(field)
        key = "%s-%s" % (parent_field_name, key) if parent_field_name else key
        if not header_dict.get(key):
            header_dict.update({key: field.label})


def get_field_by_attribute_value(form_model, key_attribute, attribute_label):
    # ex: field1.name='first_name' field1.code='q1'
    # field2.name='location' field2.code='q3'
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
        doc = EntityFormModelDocument.wrap(rows[0]['doc'])
        return EntityFormModel.new_from_doc(dbm, doc)
    return None


def get_form_code_by_entity_type(dbm, entity_type):
    form_model = get_form_model_by_entity_type(dbm, entity_type)
    return form_model.form_code if form_model else None


class FormModel(DataObject):
    __document_class__ = FormModelDocument

    @classmethod
    def new_from_doc(cls, dbm, doc):
        form_model = super(FormModel, cls).new_from_doc(dbm, doc)
        form_model._old_doc = copy.deepcopy(form_model._doc)
        return form_model

    def _set_doc(self, form_code, is_registration_model, label, language, name):
        doc = FormModelDocument()
        doc.name = name
        doc.set_label(label)
        doc.form_code = form_code
        doc.active_languages = [language]
        doc.is_registration_model = is_registration_model
        DataObject._set_document(self, doc)

    def __init__(self, dbm, name=None, label=None, form_code=None, fields=None,
                 language="en", is_registration_model=False, validators=None,
                 enforce_unique_labels=True):
        if not validators: validators = [MandatoryValidator()]
        assert isinstance(dbm, DatabaseManager)
        assert name is None or is_not_empty(name)
        assert fields is None or is_sequence(fields)
        assert form_code is None or (is_string(form_code) and is_not_empty(form_code))
        # assert type is None or is_not_empty(type)

        DataObject.__init__(self, dbm)
        self._old_doc = None

        self._snapshots = {}
        self._form_fields = []
        self.errors = []
        self.validators = validators
        self._enforce_unique_labels = enforce_unique_labels
        self._validation_exception = []
        # Are we being constructed from scratch or existing doc?
        if name is None:
            return

        # Not made from existing doc, so build ourselves up
        self._validate_fields(fields)
        self._form_fields = fields

        self._set_doc(form_code, is_registration_model, label, language, name)

    @property
    def name(self):
        """
        Returns the name of the FormModel
        """
        return self._doc.name

    @property
    def id(self):
        return self._doc.id

    @name.setter
    def name(self, value):
        """
        Sets the name of the FormModel
        """
        self._doc.name = value

    def _get_entity_questions(self, form_fields):
        ef = []
        for field in form_fields:
            if isinstance(field, UniqueIdField):
                ef.append(field)
            elif isinstance(field, FieldSet):
                ef.extend(self._get_entity_questions(field.fields))
        return ef

    @property
    def entity_questions(self):
        return self._get_entity_questions(self._form_fields)

    def _get_parent_node(self, root_node, field_code):
        field = self.get_field_by_code(field_code)
        if field.parent_field_code:
            parent_node = self._get_parent_node(root_node, field.parent_field_code)
            return self.get_field_node(parent_node, field.code, field.fieldset_type)
        return self.get_field_node(root_node, field.code, field.fieldset_type)

    def get_field_node(self, root_node, field_code, type='select1'):
        if type == 'repeat':
            repeats_group_node = self._get_node(root_node, field_code, 'group')
            return repeats_group_node._children[1]
        else:
            return self._get_node(root_node, field_code, type)

    def _get_node(self, root_node, field_code, type='select1'):
        for child in root_node:
            if child.tag.endswith(type) and child.attrib['ref'].endswith(field_code):
                return child

    def _get_choice_elements(self, options):
        choice_elements = []
        for option in options:
            node = ET.Element('{http://www.w3.org/2002/xforms}item')
            name = ET.Element('{http://www.w3.org/2002/xforms}label')
            name.text = option[1] + ' (' + option[0] + ')'
            node.append(name)
            label = ET.Element('{http://www.w3.org/2002/xforms}value')
            label.text = option[0]
            node.append(label)
            choice_elements.append(node)
        return choice_elements

    def _update_xform_with_unique_id_choices(self, root_node, uniqueid_ui_field):
        if uniqueid_ui_field.parent_field_code:
            parent_node = self._get_parent_node(root_node, uniqueid_ui_field.parent_field_code)
            node = self._get_node(parent_node, uniqueid_ui_field.code)
        else:
            node = self._get_node(root_node, uniqueid_ui_field.code)
        node.remove(node._children[1])  # removing the placeholder option
        choice_elements = self._get_choice_elements(uniqueid_ui_field.options)
        for element in choice_elements:
            node.append(element)

    def xform_with_unique_ids_substituted(self):
        root_node = ET.fromstring(self.xform)
        html_body_node = root_node._children[1]
        for entity_question in self.entity_questions:
            uniqueid_ui_field = UniqueIdUIField(entity_question, self._dbm)
            self._update_xform_with_unique_id_choices(html_body_node, uniqueid_ui_field)
        return ET.tostring(root_node)

    @property
    def is_media_type_fields_present(self):
        is_media = self._doc.is_media_type_fields_present
        return False if is_media is None else is_media

    def update_media_field_flag(self):
        if self.media_fields:
            self._doc.is_media_type_fields_present = True
        else:
            self._doc.is_media_type_fields_present = False

    def is_part_of_repeat_field(self, field):
        if field.parent_field_code:
            parent_field = self.get_field_by_code(field.parent_field_code)
            if self.is_part_of_repeat_field(parent_field):
                return True
            return parent_field.is_field_set and not parent_field.is_group()
        return False

    @property
    def xform(self):
        return self._doc.xform

    def update_xform_with_questionnaire_name(self, questionnaire_name):
        # Escape <, > and & and convert accented characters to equivalent non-accented characters
        self.xform = re.sub(r"<html:title>.+</html:", "<html:title>%s</html:" % unicodedata.normalize('NFD', escape(
            unicode(questionnaire_name))).encode('ascii', 'ignore'), self.xform)

    @xform.setter
    def xform(self, value):
        self._doc.xform = value

    @property
    def entity_type(self):
        unique_id_fields = self.entity_questions
        if unique_id_fields:
            # There can be multiple fields with similar unique id types. we need set of unique id types.
            entity_types = OrderedDict()
            for unique_id_field in unique_id_fields:
                entity_types.update({unique_id_field.unique_id_type: None})
            return entity_types.keys()
        else:
            return []

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
    def has_nested_fields(self):
        return filter(lambda f: f.is_field_set, self.fields)

    @property
    def choice_fields(self):
        return [field for field in self._form_fields if field.type in ("select", "select1")]

    @property
    def date_fields(self):
        return [field for field in self._form_fields if field.type == 'date']

    @property
    def media_fields(self):
        return self._get_media_fields(self._form_fields)

    def _get_media_fields(self, fields):
        media_fields = []
        for field in fields:
            if isinstance(field, MediaField):
                media_fields.append(field)
            if isinstance(field, FieldSet):
                media_fields_from_field_set = self._get_media_fields(field.fields)
                if media_fields_from_field_set:
                    media_fields.extend(media_fields_from_field_set)
        return media_fields

    @property
    def label(self):
        return self._doc.label

    @property
    def activeLanguages(self):
        return self._doc.active_languages

    @activeLanguages.setter
    def activeLanguages(self, value):
        self._doc.active_languages = value

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

    def save(self, process_post_update=True):
        # convert fields and validators to json fields before save
        self.check_if_form_model_unique()
        return self.update_doc_and_save(process_post_update)

    def check_if_form_model_unique(self):
        if not self.is_form_code_unique():
            raise DataObjectAlreadyExists('Form Model', 'Form Code', self.form_code)

    def update_doc_and_save(self, process_post_update=True):
        self._doc.json_fields = [f._to_json() for f in self._form_fields]
        self._doc.validators = [validator.to_json() for validator in self.validators]
        json_snapshots = {}
        for key, value in self._snapshots.items():
            json_snapshots[key] = [each._to_json() for each in value]
        self._doc.snapshots = json_snapshots
        self._delete_form_model_from_cache()
        if self._doc is None:
            raise NoDocumentError('No document to save')
        return self._dbm._save_document(self._doc, prev_doc=self._old_doc, process_post_update=process_post_update)

    def update_attachments(self, attachments, attachment_name=None):
        return self.put_attachment(self._doc, attachments, filename=attachment_name)

    def add_attachments(self, attachments, attachment_name=None):
        return self.put_attachment(self._doc, attachments, filename=attachment_name)

    def get_attachments(self, attachment_name=None):
        return self.get_attachment(self._doc.id, filename=attachment_name)

    def get_field_by_name(self, name):
        for field in self._form_fields:
            if field.name == name:
                return field
        return None

    def get_field_by_code(self, code):
        return self._get_by_code(self._form_fields, code)

    def get_field_by_code_in_fieldset(self, code, parent_code):
        parent_field = self.get_field_by_code(parent_code)
        return self._get_by_code(parent_field.fields, code)

    def _get_by_code(self, fields, code):
        for field in fields:
            if code is not None and field.code.lower() == code.lower():
                return field
            if isinstance(field, FieldSet):
                field_by_code = self._get_by_code(field.fields, code)
                if field_by_code:
                    return field_by_code
        return None

    def get_field_by_code_and_rev(self, code, revision=None):
        if self.revision == revision or not self._snapshots:
            return self.get_field_by_code(code)

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
            field_code_label_dict.update({form_field.code: quoted_label})
        return field_code_label_dict

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

    def is_entity_registration_form(self):
        return False

    def bind(self, submission):
        self.submission = submission
        for field in self.fields:
            answer = self._lookup_answer_for_field_code(self.submission, field.code)
            field.set_value(answer)

    def bound_values(self):
        values = {}
        for field in self.fields:
            values.update({field.code: field.value})
        return values

    def _validate_fields(self, fields):
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

    def _validate_answer_for_field(self, answer, field):
        try:
            value = field.validate(answer)
            return True, value
        except Exception as e:
            field.errors.append(e.message)
            self._validation_exception.append(e)
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

    def is_form_code_unique(self):
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
        key_value_items = OrderedDict([(k, v) for k, v in answers.items() if self.get_field_by_code(k) is not None])

        return key_value_items

    # TODO : does not handle value errors. eg. Text for Number. Done outside the service right now.
    def validate_submission(self, values):
        assert values is not None
        cleaned_values = OrderedDict()
        errors = OrderedDict()
        if not self.xform:
            for validator in self.validators:
                validator_error = validator.validate(values, self.fields, self._dbm)
                if hasattr(validator, 'exception'):
                    self._validation_exception.extend(getattr(validator, 'exception'))
                errors.update(validator_error)
        values = self._remove_empty_values(values)
        values = self._remove_unknown_fields(values)
        for key in values:
            field = self.get_field_by_code(key)
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

    def _lookup_answer_for_field_code(self, values, code):
        value = self._case_insensitive_lookup(values, code)
        return value

    def stringify(self, values):
        self.bind(values)
        dict = OrderedDict()
        for field in self.fields:
            dict[field.code] = field.stringify()

        return dict

    def add_validator(self, validator_class):
        if validator_class not in [validator.__class__ for validator in self.validators]:
            self.validators.append(validator_class())

    def remove_validator(self, validator_class):
        for validator in self.validators:
            if isinstance(validator, validator_class):
                self.validators.remove(validator)
                return

    @property
    def data_senders(self):
        return self._doc._data.get('data_senders')

    @property
    def validation_exception(self):
        return self._validation_exception

    @property
    def is_open_survey(self):
        return self._doc.get('is_open_survey', False)


class EntityFormModel(FormModel):
    __document_class__ = EntityFormModelDocument

    def __init__(self, dbm, name=None, label=None, form_code=None, fields=None,
                 language="en", is_registration_model=False, validators=None,
                 enforce_unique_labels=True, entity_type=None):
        super(EntityFormModel, self).__init__(dbm, name, label, form_code, fields,
                                              language, is_registration_model, validators,
                                              enforce_unique_labels)
        assert entity_type is None or is_sequence(entity_type)
        if self._doc:
            self._doc.entity_type = entity_type

    @property
    def entity_type(self):
        return self._doc.entity_type

    @entity_type.setter
    def entity_type(self, value):
        self._doc.entity_type = value

    def is_entity_registration_form(self):
        return True

    def is_global_registration_form(self):
        return GLOBAL_REGISTRATION_FORM_ENTITY_TYPE in self.entity_type

    @property
    def entity_questions(self):
        eq = []
        for f in self._form_fields:
            if isinstance(f, ShortCodeField):
                eq.append(f)
        return eq

    def get_short_code(self, values):
        return self._case_insensitive_lookup(values, self.entity_questions[0].code)

    def _set_doc(self, form_code, is_registration_model, label, language, name):
        doc = EntityFormModelDocument()
        doc.name = name
        doc.set_label(label)
        doc.form_code = form_code
        doc.active_languages = [language]
        doc.is_registration_model = is_registration_model
        DataObject._set_document(self, doc)

    def get_entity_name_question_code(self):
        for f in self._form_fields:
            if f.name == 'name':
                return f.code
