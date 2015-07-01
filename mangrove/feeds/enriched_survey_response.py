from string import lower
import traceback

from mangrove.datastore.documents import EnrichedSurveyResponseDocument
from mangrove.datastore.entity import by_short_code, Contact
from mangrove.errors.MangroveException import DataObjectNotFound
from mangrove.form_model.field import DateField, SelectField, UniqueIdField


class EnrichedSurveyResponseBuilder(object):
    def __init__(self, dbm, survey_response, form_model, additional_details, logger=None, ds_mobile_number=None):
        self.ds_mobile_number = ds_mobile_number
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
                                              self.form_model.form_code, self.survey_response.form_model_revision,
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

    def _data_sender(self):
        try:
            data_sender = Contact.get(self.dbm, self.survey_response.owner_uid)
            #todo Do we need to store datasender question code information in enriched survey response?
            return self._get_data_sender_info_dict(data_sender, '')
        except:
            return {'id': self.ds_mobile_number,
                    'last_name': None,
                    'mobile_number': self.ds_mobile_number,
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

    def _update_entity_answer_in_dictionary(self, answer_dictionary, value, unique_id_type):
        answer_dictionary.update({'is_entity_question': 'true'})
        if self.form_model.entity_type != ["reporter"]:
            try:
                subject = by_short_code(self.dbm, value, [unique_id_type])
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
            answer_dictionary.update({'unique_id_type': field.unique_id_type})
            self._update_entity_answer_in_dictionary(answer_dictionary, value, field.unique_id_type)
        #if field.code == self.form_model.entity_question.code:
        return answer_dictionary

    def _select_field_values(self, choices, field):

        # if field.has_other and isinstance(choices, list) and choices[0] == 'other':
        #     return choices[1]

        choice_array = field.get_option_list(choices)
        value_array = field.get_option_value_list(choices)
        if len(choice_array) != len(value_array):
            return {}

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
