from string import lower
from mangrove.datastore.documents import SurveyResponseEventDocument
from mangrove.form_model.field import DateField, SelectField

class SurveyResponseEventBuilder(object):
    def __init__(self, survey_response, form_model, additional_details, logger=None):
        assert additional_details is not None
        self.additional_details = additional_details
        self.survey_response = survey_response
        self.form_model = form_model
        self.logger = logger
        self.lower_case_dict = LowerCaseKeyDict(self.survey_response.values)


    def event_document(self):
        values = {}
        for field in self.form_model.fields:
            answer_dictionary = self._create_answer_dictionary(field)
            values.update({lower(field.code): answer_dictionary})

        status = 'success' if self.survey_response.status else 'error'

        return SurveyResponseEventDocument(self.survey_response.channel, self.survey_response.form_code,
            self.survey_response.form_model_revision, values, status, self.survey_response.errors,
            self.survey_response.test, self.additional_details.get('data_sender'),
            self.additional_details.get('project'))

    def _create_answer_dictionary(self, field):
        answer_dictionary = {}
        value = self.lower_case_dict.get(field.code)
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
        return answer_dictionary

    def _select_field_values(self, choices, field):
        selected = {}
        for choice in choices:
            option_value = self._option_value(field, choice)
            if option_value is None:
                error_message = 'Survey Response Id : %s, ' % self.survey_response._doc.id
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
