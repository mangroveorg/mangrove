from string import lower
import traceback
from mangrove.datastore.documents import EnrichedSurveyResponseDocument
from mangrove.datastore.entity import by_short_code, Entity, get_by_short_code_include_voided
from mangrove.errors.MangroveException import DataObjectNotFound
from mangrove.form_model.field import DateField, SelectField, UniqueIdField


class EnrichedSurveyResponseBuilder(object):
    def __init__(self, dbm, survey_response, form_model, additional_details, logger=None):
        self.dbm = dbm
        self.additional_details = additional_details
        self.survey_response = survey_response
        self.form_model = form_model
        self.logger = logger
        self.values_lower_case_dict = LowerCaseKeyDict(self.survey_response.values)


    def _values(self):
        values = {}
        if self.survey_response.status:
            for field in self.form_model.fields:
                answer_dictionary = self._create_answer_dictionary(field)
                values.update({lower(field.code): answer_dictionary})
        else:
            values = self.survey_response.values
        return values

    def feed_document(self):
        status = 'success' if self.survey_response.status else 'error'

        return EnrichedSurveyResponseDocument(self.survey_response.uuid, self.survey_response.modified,
                                              self.survey_response.channel,
                                              self.survey_response.form_code, self.survey_response.form_model_revision,
                                              self._values(), status,
                                              self.survey_response.errors, self._data_sender(), self.additional_details,
                                              self.survey_response.is_void())


    def update_event_document(self, feeds_dbm):
        enriched_survey_response = get_feed_document_by_id(feeds_dbm, self.survey_response.uuid)
        self._update_feed_with_latest_info(enriched_survey_response)
        return enriched_survey_response

    def delete_feed_document(self, feeds_dbm):
        error = None
        try:
            enriched_survey_response = get_feed_document_by_id(feeds_dbm, self.survey_response.uuid)
            self._update_feed_with_latest_info(enriched_survey_response)
            enriched_survey_response.delete()
            feeds_dbm._save_document(enriched_survey_response)
        except Exception as e:
            error = 'error while deleting feed doc for %s \n' % self.survey_response.uuid
            error += e.message + '\n'
            error += traceback.format_exc()
        finally:
            return error

    def _update_feed_with_latest_info(self, enriched_survey_response):
        enriched_survey_response.update(self.feed_document())

    def _reporter_question_code(self):
        for field in self.form_model.fields:
            if field.code == self.form_model.entity_question.code and self.form_model.entity_type[0] == 'reporter':
                return field.code.lower()
        return ''

    def _data_sender(self):
        try:
            data_sender = Entity.get(self.dbm, self.survey_response.owner_uid)
            return self._get_data_sender_info_dict(data_sender, self._reporter_question_code())
        except:
            #This will only happen during migration when introducing the feeds feature
            return {'id': None,
                    'last_name': None,
                    'mobile_number': None,
                    'question_code': None,
                    'deleted': None
            }


    def _get_data_sender_info_dict(self, data_sender, question_code):
        return {'id': data_sender.short_code,
                'last_name': data_sender.data['name']['value'],
                'mobile_number': data_sender.data['mobile_number']['value'],
                'question_code': question_code,
                'deleted': data_sender.is_void()
        }

    def _update_entity_answer_in_dictionary(self, answer_dictionary, value):
        answer_dictionary.update({'is_entity_question': 'true'})
        if self.form_model.entity_type != ["reporter"]:
            try:
                subject = by_short_code(self.dbm, value, self.form_model.entity_type)
                answer_dictionary.update(
                    {'answer': {'id': value, 'name': subject.data['name']['value'], 'deleted': False}})
            except DataObjectNotFound:
                answer_dictionary.update(
                    {'answer': {'id': value, 'name': '', 'deleted': True}})


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
        if isinstance(field, UniqueIdField):
            self._update_entity_answer_in_dictionary(answer_dictionary, value)
        #if field.code == self.form_model.entity_question.code:
        return answer_dictionary

    def _select_field_values(self, choices, field):
        choice_array = field.get_option_list(choices)
        value_array = field.get_option_value_list(choices)
        if len(choice_array) != len(value_array):
            error_message = 'Survey Response Id : %s, ' % self.survey_response.id
            error_message += 'field code %s, ' % field.code
            error_message += 'number of values not equal to number of selected choices: %s' % choices
            if self.logger: self.logger.error(error_message)
            raise Exception(error_message)

        selected = {}
        for i in range(len(choice_array)):
            selected.update({choice_array[i]: value_array[i]})
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


def get_feed_document_by_id(feed_dbm, survey_response_id):
    return feed_dbm._load_document(survey_response_id, EnrichedSurveyResponseDocument)
