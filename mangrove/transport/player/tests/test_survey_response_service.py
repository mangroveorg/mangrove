from unittest import TestCase
from mock import Mock, patch, call
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.errors.MangroveException import FormModelDoesNotExistsException
from mangrove.transport import Request
from mangrove.transport.player.parser import WebParser
from mangrove.transport.services.survey_response_service import SurveyResponseService

class TestWebPlayer2(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)

    def test_create_submission_for_a_survey_response_for_non_existent_form_code(self):
        with patch('mangrove.form_model.form_model.get_form_model_by_code') as patched_form_model:
            patched_form_model.return_value = FormModelDoesNotExistsException('form_code')
            #            patched_form_model.return_value =
            parser = Mock(spec=WebParser)

            parser.parse.return_value = ['form_code', {'q1': 'a1', 'q2': 'a2'}]
            SurveyResponseService.PARSERS = {'web': parser}
            web_player = SurveyResponseService(self.dbm)
            request = Request('', 'web')
            self.dbm._save_document.return_value = SubmissionLogDocument()
            try:
                web_player.save_survey_response(request)
                self.fail(
                    'get_form_model_by_code should have thrown exception as that is the way we have set it up and its called twice with the second call leading to exception propagation')
            except FormModelDoesNotExistsException:
                pass
            calls = [call('form_code'), call('form_code')]
            patched_form_model.assert_has_calls(calls)
