from string import lower
from mangrove.datastore.documents import EnrichedSurveyResponseDocument
from mangrove.datastore.entity import by_short_code
from mangrove.form_model.field import DateField, SelectField


class EnrichedSurveyResponseBuilder(object):
    def __init__(self, dbm, survey_response, form_model, reporter_id, additional_details, logger=None):
        self.dbm = dbm
        self.reporter_id = reporter_id
        self.additional_details = additional_details
        self.survey_response = survey_response
        self.form_model = form_model
        self.logger = logger
        self.values_lower_case_dict = LowerCaseKeyDict(self.survey_response.values)


    def event_document(self):
        values = {}
        for field in self.form_model.fields:
            answer_dictionary = self._create_answer_dictionary(field)
            values.update({lower(field.code): answer_dictionary})

        status = 'success' if self.survey_response.status else 'error'

        return EnrichedSurveyResponseDocument(self.survey_response.uuid, self.survey_response.channel,
            self.survey_response.form_code, self.survey_response.form_model_revision, values, status,
            self.survey_response.errors, self._data_sender(), self.additional_details, self.survey_response.is_void())

    def _data_sender(self):
        data_sender_id = self.reporter_id
        for field in self.form_model.fields:
            if field.code == self.form_model.entity_question.code and self.form_model.entity_type[0] == 'reporter':
                data_sender_id = self.values_lower_case_dict.get(field.code)
                break

        data_sender = by_short_code(self.dbm, data_sender_id, ['reporter'])
        return {'id': data_sender_id,
                'last_name': data_sender.data['name']['value'],
                'mobile_number': data_sender.data['mobile_number']['value']}

    def _create_answer_dictionary(self, field):
        answer_dictionary = {}
        value = self.values_lower_case_dict.get(field.code)
        answer_dictionary.update({'label': field.label})
        answer_dictionary.update({'type': field.type})
        answer_dictionary.update({'answer': value})
        if isinstance(field, DateField):
            answer_dictionary.update({'format': field.date_format})
        if isinstance(field, SelectField):
            selected = self._select_field_values(answer_dictionary.get('answer'), field)
            answer_dictionary.update({'answer': selected})
        if field.code == self.form_model.entity_question.code:
            answer_dictionary.update({'is_entity_question': 'true'})
            if self.form_model.entity_type != "reporter":
                subject = by_short_code(self.dbm, value, self.form_model.entity_type)
                answer_dictionary.update(
                    {'answer': {value: subject.data['name']['value']}})
        return answer_dictionary

    def _select_field_values(self, choices, field):
        selected = {}
        for choice in choices:
            option_value = self._option_value(field, choice)
            if option_value is None:
                error_message = 'Survey Response Id : %s, ' % self.survey_response.id
                error_message += 'field code %s, ' % field.code
                error_message += 'value not found for selected choice %s' % choice
                if self.logger: self.logger.error(error_message)
                raise Exception(error_message)
            selected.update({choice: option_value})
        return selected

    def _option_value(self, field, value):
        for option in field.options:
            if option.get('val') == value:
                return option.get('text')
        return None


class LowerCaseKeyDict():
    def __init__(self, input_dict):
        self.dictionary = {}
        for key, value in input_dict.iteritems():
            self.dictionary.update({lower(key): value})

    def get(self, key):
        return None if key is None else self.dictionary.get(lower(key))

