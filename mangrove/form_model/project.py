from collections import OrderedDict
from datetime import timedelta

from mangrove.datastore.database import DatabaseManager, DataObject
from mangrove.datastore.documents import ProjectDocument
from mangrove.datastore.entity import from_row_to_entity, Contact
from mangrove.errors.MangroveException import DataObjectAlreadyExists, FormModelDoesNotExistsException, \
    ProjectPollCodeDoesNotExistsException
from mangrove.form_model.deadline import Deadline, Month, Week
from mangrove.form_model.form_model import REPORTER, get_form_model_by_code, FormModel, get_form_model_document
from mangrove.transport.repository.reporters import get_reporters_who_submitted_data_for_frequency_period
from mangrove.datastore.user_questionnaire_preference import UserQuestionnairePreference, \
    UserQuestionnairePreferenceDocument
from mangrove.form_model.form_model import get_form_model_fields_by_entity_type


def get_project_by_code(dbm, code):
    row_value = get_form_model_document(code, dbm)

    return Project.new_from_doc(dbm, ProjectDocument.wrap(row_value))


default_reminder_and_deadline = {"deadline_type": "Following", "should_send_reminder_to_all_ds": False,
                                 "has_deadline": True,
                                 "deadline_month": "5", "frequency_period": "month"}


class Project(FormModel):
    __document_class__ = ProjectDocument

    def _set_doc(self, form_code, is_registration_model, label, language, name):
        doc = ProjectDocument()
        doc.name = name
        doc.set_label(label)
        doc.form_code = form_code
        doc.active_languages = [language]
        doc.is_registration_model = is_registration_model
        DataObject._set_document(self, doc)

    def __init__(self, dbm, form_code=None, name=None, goals="", devices=None, sender_group=None, is_poll=False,
                 end_date=None, active=None,
                 language='en', fields=[]):
        FormModel.__init__(self, dbm=dbm, form_code=form_code, is_registration_model=False,
                           label="", language=language, name=name, fields=fields)
        if self._doc:
            self._doc.goals = goals
            self._doc.devices = devices
            self._doc.sender_group = sender_group
            self._doc.reminder_and_deadline = default_reminder_and_deadline
            self._doc.is_poll = is_poll
            self._doc.end_date = end_date
            self._doc.active = active

    @classmethod
    def from_form_model(cls, form_model):
        return super(Project, cls).new_from_doc(form_model._dbm, ProjectDocument.wrap(form_model._doc._data))

    @property
    def data_senders(self):
        return self._doc.data_senders

    @property
    def goals(self):
        return self._doc.goals

    @property
    def is_poll(self):
        is_poll = self._doc.is_poll
        return False if is_poll is None else is_poll

    @property
    def modified(self):
        return self._doc.modified

    @property
    def end_date(self):
        end_date = self._doc.end_date
        return False if end_date is None else end_date

    @property
    def active(self):
        active = self._doc.active
        return False if active is None else active == 'active'

    @end_date.setter
    def end_date(self, end_date):
        self._doc.end_date = end_date

    @active.setter
    def active(self, active):
        self._doc.active = active

    @data_senders.setter
    def data_senders(self, value):
        self._doc.data_senders = value

    @property
    def devices(self):
        return self._doc.devices

    @property
    def language(self):
        return self.activeLanguages[0]

    @property
    def is_outgoing_sms_replies_enabled(self):
        is_enabled = self._doc.is_outgoing_sms_replies_enabled
        return True if is_enabled is None else is_enabled

    @is_outgoing_sms_replies_enabled.setter
    def is_outgoing_sms_replies_enabled(self, enable_replies):
        self._doc.is_outgoing_sms_replies_enabled = enable_replies

    @property
    def reminder_and_deadline(self):
        return self._doc.reminder_and_deadline

    @reminder_and_deadline.setter
    def reminder_and_deadline(self, value):
        self._doc.reminder_and_deadline = value

    def reset_reminder_and_deadline(self):
        self.reminder_and_deadline = default_reminder_and_deadline

    def get_data_senders(self, dbm):
        all_data, fields, label = load_data_senders(dbm, self.data_senders)
        return [dict(zip(fields, data["cols"])) for data in all_data]

    def get_associated_datasenders(self, dbm):
        keys = [([REPORTER], short_code) for short_code in self.data_senders]
        rows = dbm.view.by_short_codes(reduce=False, include_docs=True, keys=keys)
        return [Contact.new_from_doc(dbm, Contact.__document_class__.wrap(row.get('doc'))) for row in rows]

    def _get_data_senders_ids_who_made_submission_for(self, dbm, deadline_date, frequency_period):
        if frequency_period == 'month':
            start_date, end_date = deadline_date - timedelta(days=7), deadline_date + timedelta(days=7)
        else:
            start_date, end_date = deadline_date - timedelta(days=3), deadline_date + timedelta(days=3)
        form_model_id = self.id
        data_senders_with_submission = get_reporters_who_submitted_data_for_frequency_period(dbm, form_model_id,
                                                                                             start_date,
                                                                                             end_date)
        return [datasender.short_code for datasender in data_senders_with_submission]

    def get_data_senders_without_submissions_for(self, deadline_date, dbm, frequency_period):
        data_sender_ids_with_submission = self._get_data_senders_ids_who_made_submission_for(dbm, deadline_date,
                                                                                             frequency_period)
        my_data_senders = self.get_data_senders(dbm)
        data_senders_without_submission = [data_sender for data_sender in my_data_senders if
                                           data_sender['short_code'] not in data_sender_ids_with_submission]
        return data_senders_without_submission

    def deadline(self):
        return Deadline(self._frequency(), self._deadline_type())

    def _frequency(self):
        if self.reminder_and_deadline.get('frequency_period') == 'month':
            return Month(int(self.reminder_and_deadline.get('deadline_month')))
        if self.reminder_and_deadline.get('frequency_period') == 'week':
            return Week(int(self.reminder_and_deadline.get('deadline_week')))

    def has_deadline(self):
        return self.reminder_and_deadline.get('has_deadline')

    def _deadline_type(self):
        return self.reminder_and_deadline.get('deadline_type')

    def _frequency_period(self):
        return self.reminder_and_deadline.get('frequency_period')

    def get_deadline_day(self):
        if self.reminder_and_deadline.get('frequency_period') == 'month':
            return int(self.reminder_and_deadline.get('deadline_month'))

    def should_send_reminders(self, as_of, days_relative_to_deadline):
        next_deadline_day = self.deadline().current(as_of)
        if next_deadline_day is not None:
            if as_of == next_deadline_day + timedelta(days=days_relative_to_deadline):
                return True
        return False

    def is_project_name_unique(self):
        rows = self._dbm.load_all_rows_in_view('project_names', key=self.name.lower())
        if len(rows) and rows[0]['value']["id"] != self.id:
            return False
        return True

    def _check_if_project_name_unique(self):
        if not self.is_project_name_unique():
            raise DataObjectAlreadyExists('Questionnaire', "Name", "'%s'" % self.name)

    def save(self, process_post_update=True):
        assert isinstance(self._dbm, DatabaseManager)
        self._check_if_project_name_unique()
        return super(Project, self).save(process_post_update)

    def update(self, value_dict):
        attribute_list = [item[0] for item in (self._doc.items())]
        for key in value_dict:
            if key in attribute_list:
                setattr(self._doc, key, value_dict.get(key))

    def set_void(self, void=True):
        self._doc.void = void

    def delete_datasender(self, dbm, entity_id):
        if entity_id in self.data_senders:
            self.data_senders.remove(entity_id)
            self.save(process_post_update=False)

    def _remove_duplicate_datasenders(self, data_senders_list):
        datasenders_already_linked_to_questionnaire = []
        for data_senders_code in data_senders_list:
            if data_senders_code in self.data_senders:
                # data_senders_list.remove(data_senders_code)
                datasenders_already_linked_to_questionnaire.append(data_senders_code)
        for ds in datasenders_already_linked_to_questionnaire:
            data_senders_list.remove(ds)

    def associate_data_sender_to_project(self, dbm, data_senders_list):
        self._remove_duplicate_datasenders(data_senders_list)
        # from datawinners.search.datasender_index import update_datasender_index_by_id
        # Normally this case should not happen. However in a special case
        # blank id was sent from client side. So introduced this check.
        if data_senders_list:
            self.data_senders.extend(data_senders_list)
            self.save(process_post_update=False)

    @property
    def is_open_survey(self):
        return self._doc.is_open_survey

    @is_open_survey.setter
    def is_open_survey(self, value):
        self._doc.is_open_survey = value

    def has_attachment(self):
        try:  # find a better way to check attachement exisits
            attachment = self.get_attachments('questionnaire.xls')
            return True, attachment, 'xls'
        except LookupError:
            try:
                attachment = self.get_attachments('questionnaire.xlsx')
                return True, attachment, 'xlsx'
            except LookupError:
                return False, None, None

    def has_external_itemset(self):
        try:  # find a better way to check attachement exisits
            attachment = self.get_attachments('itemsets.csv')
            return True, attachment, 'csv'
        except LookupError:
            return False, None, None

    def update_attachments(self, attachments, attachment_name):
        extension = self.has_attachment()[2]
        self.delete_attachment(self._doc, "questionnaire%s" % extension)
        self.add_attachments(attachments, attachment_name)

    def update_external_itemset(self, itemset):
        if len(self.external_choice_questions) == 0 and self.has_external_itemset():
            self.delete_attachment(self._doc, "itemsets.csv")
        if itemset and self.has_external_itemset():
            self.delete_attachment(self._doc, "itemsets.csv")
            self.add_attachments(itemset, "itemsets.csv")
        elif itemset:
            self.add_attachments(itemset, "itemsets.csv")


def load_data_senders(manager, short_codes):
    form_model = get_form_model_by_code(manager, 'reg')
    fields, labels, codes = get_entity_type_fields(manager)
    keys = [([REPORTER], short_code) for short_code in short_codes]
    rows = manager.view.by_short_codes(reduce=False, include_docs=True, keys=keys)
    data = [tabulate_data(from_row_to_entity(manager, row), form_model, codes) for row in rows]
    return data, fields, labels


def get_entity_type_fields(manager, form_code='reg', form_model=None):
    if form_model is None:
        form_model = get_form_model_by_code(manager, form_code)
    json_fields = form_model._doc["json_fields"]
    return get_json_field_infos(json_fields)


def get_json_field_infos(fields):
    fields_names, labels, codes = [], [], []
    for field in fields:
        if field['name'] not in ['entity_type', 'is_data_sender']:
            fields_names.append(field['name'])
            labels.append(field['label'])
            codes.append(field['code'])
    return fields_names, labels, codes


def tabulate_data(entity, form_model, field_codes):
    data = {'id': entity.id, 'short_code': entity.short_code}

    dict = OrderedDict()
    for field in form_model.fields:
        if field.name in entity.data:
            dict[field.code] = get_field_value(field.name, entity)
        else:
            dict[field.code] = get_field_default_value(field.name, entity)

    stringified_dict = form_model.stringify(dict)

    data['cols'] = [stringified_dict[field_code] for field_code in field_codes]
    return data


def get_field_value(key, entity):
    value = entity.value(key)
    if key == 'geo_code':
        if value is None:
            return entity.geometry.get('coordinates')
    elif key == 'location':
        if value is None:
            return entity.location_path

    return value


def get_field_default_value(key, entity):
    if key == 'geo_code':
        return entity.geometry.get('coordinates')
    if key == 'location':
        return entity.location_path
    if key == 'short_code':
        return entity.short_code
    return None


def get_active_form_model(dbm, form_code):
    projects = dbm.load_all_rows_in_view("all_projects")
    for project_row in projects:
        project_doc = ProjectDocument.wrap(project_row.get('value'))
        project = Project.new_from_doc(dbm, project_doc)
        if project.active:
            return project
    raise FormModelDoesNotExistsException(form_code)


def check_if_form_code_is_poll(self, form_model):
    if form_model:
        project = get_project_by_code(self.dbm, form_model.form_code)
        if project and project.is_poll is True:
            raise ProjectPollCodeDoesNotExistsException(project.form_code)


def get_active_form_model_name_and_id(dbm):
    projects = dbm.load_all_rows_in_view("all_projects")
    for project_row in projects:
        project_doc = ProjectDocument.wrap(project_row.get('value'))
        project = Project.new_from_doc(dbm, project_doc)
        if project.active:
            return True, project.id, project.name
    return False, "", ""
