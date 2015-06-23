
from collections import OrderedDict
from unittest.case import TestCase
from mock import Mock, patch, PropertyMock, MagicMock
from mangrove.form_model.field import HierarchyField, GeoCodeField, TextField, UniqueIdField
from mangrove.form_model.form_model import LOCATION_TYPE_FIELD_NAME
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity, Contact
from mangrove.errors.MangroveException import  NumberNotRegisteredException, SMSParserInvalidFormatException, MultipleSubmissionsForSameCodeException
from mangrove.form_model.form_model import FormModel
from mangrove.form_model.project import Project
from mangrove.transport.player.parser import  OrderSMSParser
from mangrove.transport.contract.request import Request
from mangrove.transport.contract.transport_info import TransportInfo
from mangrove.transport.contract.response import Response
from mangrove.transport.player.tests.test_web_player import mock_form_submission
from mangrove.transport.player.new_players import SMSPlayerV2


class TestSMSPlayer(TestCase):

    def _mock_reporter(self):
        self.reporter_mock = MagicMock(spec=Contact)
        self.reporter_name = "1234"
        self.reporter_mock.value.return_value = self.reporter_name
        self.reporter_mock.short_code = "short_code"
        self.reporter_module.find_reporter_entity.return_value = self.reporter_mock


    def setUp(self):
        self.loc_tree = Mock()
        self.loc_tree.get_hierarchy_path.return_value = None
        self.dbm = Mock(spec=DatabaseManager)
        self._mock_form_model()
        self.reporter_patcher = patch('mangrove.transport.player.new_players.reporters')
        self.reporter_module = self.reporter_patcher.start()
        self._mock_reporter()
        self.transport = TransportInfo(transport="sms", source="1234", destination="5678")
        self.message = "FORM_CODE .ID 1 .M hello world"
        self.generate_code_patcher = patch(
            "mangrove.transport.work_flow._set_short_code")
        self.generate_code_patcher.start()

        self.post_sms_processor_mock = Mock()
        self.post_sms_processor_mock.process = lambda x, y, z=None: None
        self.post_sms_processors = [self.post_sms_processor_mock]

        self.sms_player = SMSPlayerV2(self.dbm, self.post_sms_processors)

    @staticmethod
    def mocked_post_sms_processor():
        return

    def _mock_form_model(self):
        self.get_form_model_mock_player_patcher = patch(
            'mangrove.transport.services.survey_response_service.get_form_model_by_code')
        self.get_form_model_mock_parser_patcher = patch('mangrove.transport.player.parser.get_form_model_by_code')
        # self.get_form_model_mock_player_v2_patcher = patch('mangrove.transport.player.new_players.get_form_model_by_code')
        get_form_model_player_mock = self.get_form_model_mock_player_patcher.start()
        get_form_model_parser_mock = self.get_form_model_mock_parser_patcher.start()
        # get_form_model_player_v2_mock = self.get_form_model_mock_player_v2_patcher.start()
        self.form_model_mock = MagicMock(spec=FormModel)
        self.form_model_mock.is_entity_registration_form.return_value = True
        self.form_model_mock.entity_type = ["clinic"]
        self.form_model_mock.get_field_by_name = self._location_field
        field = UniqueIdField('clinic','q1', 'id', 'q1')
        self.form_model_mock.fields = [field]
        self.form_model_mock.is_open_survey = False
        self.form_model_mock.validate_submission.return_value = OrderedDict(), OrderedDict()

        self.form_submission_mock = mock_form_submission(self.form_model_mock)

        get_form_model_player_mock.return_value = self.form_model_mock
        get_form_model_parser_mock.return_value = self.form_model_mock
        # get_form_model_player_v2_mock.return_value = self.form_model_mock


    def _location_field(self, *args, **kwargs):
        name = kwargs.get('name')
        if name is LOCATION_TYPE_FIELD_NAME:
            location_field = Mock(spec=HierarchyField)
            location_field.code = 'l'
            return location_field
        geo_code_field = Mock(spec=GeoCodeField)
        geo_code_field.code = 'g'
        return geo_code_field

    def tearDown(self):
        self.reporter_patcher.stop()
        self.generate_code_patcher.stop()
        self.get_form_model_mock_player_patcher.stop()
        self.get_form_model_mock_parser_patcher.stop()


    def test_should_call_parser_post_processor_and_continue_for_no_response(self):
        self.loc_tree.get_location_hierarchy.return_value = None
        message = 'SOME_FORM_CODE 1'

        post_sms_processor_mock = Mock()
        post_sms_processors = [post_sms_processor_mock]

        sms_player = SMSPlayerV2(self.dbm, post_sms_processors)
        with patch("inspect.getargspec") as get_arg_spec_mock:
            with patch('mangrove.transport.player.new_players.SurveyResponseService.save_survey') as save_survey:
                with patch('mangrove.form_model.project.get_project_by_code') as get_project_by_code:
                 with patch('mangrove.form_model.project.check_if_form_code_is_poll') as mock_check_if_form_code_is_poll:
                    get_arg_spec_mock.return_value = (['self', 'form_code', 'submission_values', 'extra_elements'], )

                    sms_player.add_survey_response(Request(message=message, transportInfo=self.transport))

                    save_survey.assert_called_once('some_form_code', {'id': '1'}, [{'name': '1234'}], 'sms', message)
                    post_sms_processor_mock.process.assert_called_once_with('some_form_code', {'id': '1'}, [])

    def test_should_call_parser_post_processor_and_return_if_there_is_response_from_post_processor(self):
        parser_mock = Mock(spec=OrderSMSParser)
        parser_mock.parse.return_value = ('FORM_CODE', {'id': '1'}, [])
        parser_mock.parse.return_value = ('FORM_CODE', {'id': '1'}, [])
        post_sms_processor_mock = Mock()
        expected_response = Response(reporters=None, survey_response_id=None)
        post_sms_processor_mock.process.return_value = expected_response
        message = 'FORM_CODE 1'

        sms_player = SMSPlayerV2(self.dbm, post_sms_parser_processors=[post_sms_processor_mock])
        with patch("inspect.getargspec") as get_arg_spec_mock:
            with patch('mangrove.form_model.project.get_project_by_code') as get_project_by_code:
                with patch('mangrove.form_model.project.check_if_form_code_is_poll') as mock_check_if_form_code_is_poll:
                    get_arg_spec_mock.return_value = (['self', 'form_code', 'submission_values', 'extra_elements'], )
                    response = sms_player.add_survey_response(Request(message=message, transportInfo=self.transport))
                    self.assertEqual(expected_response, response)


    def test_should_allow_submission_by_unregistered_reporter_for_open_datasender_questionnaire(self):
        self.reporter_module.find_reporter_entity.side_effect = NumberNotRegisteredException("1234")
        self.form_model_mock.is_open_survey = True
        entity_question_field = Mock()
        entity_question_field.code = 'q1'
        self.form_model_mock.entity_questions = [entity_question_field]
        with patch('mangrove.form_model.project.get_project_by_code') as get_project_by_code:
                with patch('mangrove.form_model.project.check_if_form_code_is_poll') as mock_check_if_form_code_is_poll:
                    response = self.sms_player.add_survey_response(Request(message=self.message, transportInfo=self.transport))

                    self.assertEqual(response.errors, {})
                    self.assertTrue(response.success)



    def test_should_not_parse_if_two_question_codes(self):
        transport = TransportInfo(transport="sms", source="1234", destination="5678")
        with patch('mangrove.form_model.project.get_project_by_code') as get_project_by_code:
                with patch('mangrove.form_model.project.check_if_form_code_is_poll') as mock_check_if_form_code_is_poll:
                    with self.assertRaises(MultipleSubmissionsForSameCodeException):
                        self.sms_player.add_survey_response(
                            Request(message="cli001 .na tester1 .na tester2", transportInfo=transport))

                        self.assertEqual(0, self.form_model_mock.validate_submission.call_count)


    def test_should_accept_ordered_sms_message(self):
        self.loc_tree.get_location_hierarchy.return_value = None
        sms_message = "questionnaire_code question1_answer question2_answer"
        request = Request(transportInfo=self.transport, message=sms_message)
        with patch(
            'mangrove.transport.services.survey_response_service.SurveyResponseService.save_survey') as save_survey:
            with patch('mangrove.form_model.project.get_project_by_code') as get_project_by_code:
                with patch('mangrove.form_model.project.check_if_form_code_is_poll') as mock_check_if_form_code_is_poll:
                    mock_form_model = Mock(spec=FormModel)
                    get_project_by_code.return_value = []
                    #mock_get_form_model_by_code.return_value = mock_form_model
                    save_survey.return_value = Mock(spec=Response)
                    self.sms_player.add_survey_response(request)
                    save_survey.assert_called_once_with('questionnaire_code', {'id': 'question1_answer'}, [{'name': '1234'}],
                                                        self.transport, "short_code", additional_feed_dictionary=None,
                                                        translation_processor=None)

    def test_should_save_survey_for_a_reporter_with_no_name(self):
        self.loc_tree.get_location_hierarchy.return_value = None
        sms_message = "questionnaire_code question1_answer question2_answer"
        request = Request(transportInfo=self.transport, message=sms_message)
        contact = MagicMock(Contact)
        contact.value.return_value = None
        contact.short_code = "short_code"

        self.reporter_module.find_reporter_entity.return_value = contact
        with patch(
            'mangrove.transport.player.new_players.SurveyResponseService') as SurveyResponseServiceMock:
            with patch('mangrove.form_model.project.get_project_by_code') as get_project_by_code:
                with patch('mangrove.form_model.project.check_if_form_code_is_poll') as mock_check_if_form_code_is_poll:
                    instance_mock = Mock()
                    SurveyResponseServiceMock.return_value = instance_mock

                    self.sms_player.add_survey_response(request)

                    instance_mock.save_survey.assert_called_with('questionnaire_code', {'id': 'question1_answer'}, None,
                        self.transport, "short_code", additional_feed_dictionary=None,
                                       translation_processor=None)

