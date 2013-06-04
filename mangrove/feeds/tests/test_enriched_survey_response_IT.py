from mangrove.bootstrap import initializer
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.entity import Entity
from mangrove.datastore.tests.test_data import TestData
from mangrove.feeds.enriched_survey_response import EnrichedSurveyResponseBuilder, get_document
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.utils.test_utils.survey_response_builder import TestSurveyResponseBuilder

class TestEnrichedSurveyResponseIT(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)
        self.feed_manager = get_db_manager('http://localhost:6984/', 'feed-mangrove-test')
        _delete_db_and_remove_db_manager(self.feed_manager)
        self.feed_manager = get_db_manager('http://localhost:6984/', 'feed-mangrove-test')
        self.create_reporter()
        TestData(self.manager)

    def test_should_update_enriched_survey_response(self):
        survey_response = TestSurveyResponseBuilder(self.manager, form_code='CL1',
            values={'ID': '1', 'Q1': 'name', 'Q2': 21, 'Q3': 'a'}).build()
        form_model = get_form_model_by_code(self.manager, 'CL1')
        self.feed_manager._save_document(
            EnrichedSurveyResponseBuilder(self.manager, survey_response, form_model, 'ashwin',
                {}).event_document())
        edited_values = {'ID': '1', 'Q1': 'name2', 'Q2': 24, 'Q3': 'b'}
        survey_response.set_form(form_model)
        survey_response.set_answers('1', edited_values)
        survey_response.save()
        doc = EnrichedSurveyResponseBuilder(self.manager, survey_response, form_model, 'ashwin',
            {}).update_event_document(self.feed_manager)
        self.feed_manager._save_document(doc)
        edited_feed_document = get_document(self.feed_manager, survey_response.uuid)
        expected_values = {
            'id': {'answer': {'1': 'clinic1'}, 'is_entity_question': 'true', 'type': 'text',
                   'label': 'What is associated entity'},
            'q1': {'answer': 'name2', 'type': 'text', 'label': 'What is your name'},
            'q2': {'answer': 24, 'type': 'integer', 'label': "What is your Father's Age"},
            'q3': {'answer': {'b': 'YELLOW'}, 'type': 'select1', 'label': 'What is your favourite color'}
        }

        self.assertDictEqual(edited_feed_document.values, expected_values)


    def create_reporter(self):
        r = Entity(self.manager, entity_type=["Reporter"], short_code='ashwin')
        r.save()
        return r

