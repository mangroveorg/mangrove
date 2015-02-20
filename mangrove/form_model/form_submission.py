from collections import OrderedDict
from mangrove.datastore.documents import DataRecordDocument
from mangrove.form_model.form_model import GEO_CODE_FIELD_NAME, LOCATION_TYPE_FIELD_NAME, GEO_CODE, \
    ENTITY_TYPE_FIELD_CODE, REGISTRATION_FORM_CODE
from mangrove.form_model.location import Location
from mangrove.datastore import entity
from mangrove.utils.types import is_empty, is_not_empty


class FormSubmission(object):
    def __init__(self, form_model, form_answers, errors=None, location_tree=None):
        assert errors is None or type(errors) == OrderedDict
        assert form_answers is not None and type(form_answers) == OrderedDict
        assert form_model is not None

        self.form_model = form_model
        self._cleaned_data = form_answers
        if form_model.is_entity_registration_form():
            short_code_field = form_model.entity_questions[0].code
        else:
            short_code_field = form_model.entity_questions[0].code if form_model.entity_questions else ''
        entity_short_code = self.get_answer_for(short_code_field)
        self.short_code = entity_short_code.lower() if entity_short_code is not None else None
        entity_types = self.get_entity_type(form_model)
        self.entity_type = [entity_types[0]] if entity_types else entity_types
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
        return self.form_model.is_entity_registration_form()

    def save_new(self, dbm):
        entity = self.create_entity(dbm)
        return self._save_data(entity)

    def save(self, dbm):
        return self.save_new(dbm)

    def update(self, dbm):
        location_hierarchy, processed_geometry = Location(self.location_tree, self.form_model).process_entity_creation(
            self.cleaned_data)
        entity = self.get_entity(dbm)
        entity.set_location_and_geo_code(location_hierarchy, processed_geometry)
        return self._save_data(entity)

    def _contains_geo_code(self, item):
        item_ = item[0]
        return item_ == GEO_CODE_FIELD_NAME

    def _save_data(self, entity):
        submission_information = dict(form_code=self.form_code)
        self.data_record_id = entity.add_data(data=self._values,
                                              submission=submission_information)
        return self.data_record_id

    def _to_three_tuple(self):
        return [(self.form_model.get_field_by_code(code).name, value)
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

    def save(self, dbm):
        doc = None
        if self.short_code:
            entity = self.create_entity(dbm)
            doc = entity._doc
        submission_information = dict(form_code=self.form_code)
        data_record_doc = DataRecordDocument(
            entity_doc=doc,
            data=self._values,
            submission=submission_information
        )
        self.data_record_id = dbm._save_document(data_record_doc)
        return self.data_record_id


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
        data_records = dbm.view.data_record_by_form_code(key=[REGISTRATION_FORM_CODE, self.short_code])
        for data_record in data_records:
            data_record_doc = data_record.value
            data_record_doc['void'] = True
            dbm.database.save(data_record_doc)

    def get_entity(self, dbm):
        return entity.contact_by_short_code(dbm=dbm, short_code=self.short_code)

    def create_entity(self, dbm):
        location_hierarchy, processed_geometry = Location(self.location_tree, self.form_model).process_entity_creation(
            self.cleaned_data)
        is_datasender = self._cleaned_data.pop('is_data_sender', True)
        return entity.create_contact(dbm=dbm, contact_type=self.entity_type,
                                     location=location_hierarchy,
                                     short_code=self.short_code,
                                     geometry=processed_geometry,
                                     is_datasender=is_datasender)


class EntityRegistrationFormSubmission(FormSubmission):
    def __init__(self, form_model, answers, errors, location_tree=None):
        super(EntityRegistrationFormSubmission, self).__init__(form_model, answers, errors, location_tree=location_tree)

    # soft deletes data records
    def void_existing_data_records(self, dbm, form_code):
        data_records = dbm.view.data_record_by_form_code(key=[form_code, self.short_code])
        for data_record in data_records:
            data_record_doc = data_record.value
            data_record_doc['void'] = True
            dbm.database.save(data_record_doc)


class FormSubmissionFactory(object):
    def get_form_submission(self, form_model, answers, errors=None, location_tree=None):
        if not form_model.is_entity_registration_form():
            return DataFormSubmission(form_model, answers, errors)
        elif form_model.is_global_registration_form():  # Registering/Editing datasender
            return GlobalRegistrationFormSubmission(form_model, answers, errors, location_tree=location_tree)
        else:  # Registering/Editing subjects
            return EntityRegistrationFormSubmission(form_model, answers, errors, location_tree=location_tree)
