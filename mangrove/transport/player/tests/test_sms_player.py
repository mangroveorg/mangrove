# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from collections import OrderedDict
from unittest.case import TestCase, SkipTest
from mock import Mock, patch
from mangrove.form_model.field import HierarchyField, GeoCodeField
from mangrove.form_model.form_model import LOCATION_TYPE_FIELD_NAME, FormSubmission, FormSubmissionFactory
from mangrove.form_model.form_model import NAME_FIELD
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.errors.MangroveException import  NumberNotRegisteredException, SMSParserInvalidFormatException, MultipleSubmissionsForSameCodeException
from mangrove.form_model.form_model import FormModel
from mangrove.transport.player.parser import  OrderSMSParser
from mangrove.transport.player.player import SMSPlayer
from mangrove.transport.facade import Request, TransportInfo
from mangrove.transport.facade import Response


class TestSMSPlayer(TestCase):
    def _mock_reporter(self):
        self.reporter_mock = Mock(spec=Entity)
        self.reporter_name = "1234"
        self.reporter_mock.value.return_value = self.reporter_name
        self.reporter_module.find_reporter_entity.return_value = self.reporter_mock

    def setUp(self):
        self.loc_tree = Mock()
        self.loc_tree.get_hierarchy_path.return_value = None
        self.dbm = Mock(spec=DatabaseManager)
        self._mock_form_model()
        self.reporter_patcher = patch('mangrove.transport.player.player.reporter')
        self.reporter_module = self.reporter_patcher.start()
        self._mock_reporter()
        self.transport = TransportInfo(transport="sms", source="1234", destination="5678")
        self.message = "FORM_CODE .ID 1 .M hello world"
        self.sms_player = SMSPlayer(self.dbm, self.loc_tree)
        self.generate_code_patcher = patch(
            "mangrove.transport.facade._set_short_code")
        self.generate_code_patcher.start()

    def _mock_form_model(self):
        self.get_form_model_mock_player_patcher = patch('mangrove.transport.player.player.get_form_model_by_code')
        self.get_form_model_mock_parser_patcher = patch('mangrove.transport.player.parser.get_form_model_by_code')
        get_form_model_player_mock = self.get_form_model_mock_player_patcher.start()
        get_form_model_parser_mock = self.get_form_model_mock_parser_patcher.start()
        self.form_model_mock = Mock(spec=FormModel)
        self.form_model_mock.is_registration_form.return_value = True
        self.form_model_mock.entity_type = ["clinic"]
        self.form_model_mock.is_inactive.return_value = False
        self.form_model_mock.get_field_by_name = self._location_field
        self.form_model_mock.is_valid.return_value = OrderedDict(), OrderedDict()
        self.form_submission_mock = Mock(spec=FormSubmission)
        self.form_submission_mock.is_valid = True
        self.form_submission_mock.errors = OrderedDict()
        self.form_submission_mock.data_record_id = ''
        self.form_submission_mock.form_model = self.form_model_mock
        self.form_submission_mock.short_code = ''
        self.form_submission_mock.entity_type = ['']
        get_form_model_player_mock.return_value = self.form_model_mock
        get_form_model_parser_mock.return_value = self.form_model_mock


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

    def test_sms_player_should_parse_message(self):
        parser_mock = Mock(spec=OrderSMSParser)
        parser_mock.parse.return_value = ('FORM_CODE', {'id': '1'})
        message = 'FORM_CODE 1'

        sms_player = SMSPlayer(self.dbm, self.loc_tree, parser_mock)

        with patch.object(FormSubmissionFactory, 'get_form_submission') as get_form_submission_mock:
            get_form_submission_mock.return_value = self.form_submission_mock
            sms_player.accept(Request(message=message, transportInfo=self.transport))
            parser_mock.parse.assert_called_once_with(message)

    def test_should_call_parser_post_processor_and_continue_for_no_response(self):
        parser_mock = Mock(spec=OrderSMSParser)
        parser_mock.parse.return_value = ('FORM_CODE', {'id': '1'})
        post_sms_processor_mock = Mock()
        post_sms_processor_mock.process.return_value = None
        message = 'FORM_CODE 1'

        sms_player = SMSPlayer(self.dbm, self.loc_tree, parser=parser_mock,
            post_sms_parser_processors=[post_sms_processor_mock])
        with patch.object(FormSubmissionFactory, 'get_form_submission') as get_form_submission_mock:
            get_form_submission_mock.return_value = self.form_submission_mock
            response = sms_player.accept(Request(message=message, transportInfo=self.transport))
            self.assertEqual(self.reporter_name, response.reporters[0][NAME_FIELD])

            post_sms_processor_mock.process.assert_called_once_with('FORM_CODE', {'id': '1', 'l': None})


    def test_should_call_parser_post_processor_and_return_if_there_is_response_from_post_processor(self):
        parser_mock = Mock(spec=OrderSMSParser)
        parser_mock.parse.return_value = ('FORM_CODE', {'id': '1'})
        post_sms_processor_mock = Mock()
        expected_response = Response(reporters=None, submission_id=None, form_submission=None)
        post_sms_processor_mock.process.return_value = expected_response
        message = 'FORM_CODE 1'

        sms_player = SMSPlayer(self.dbm, self.loc_tree, parser=parser_mock,
            post_sms_parser_processors=[post_sms_processor_mock])
        response = sms_player.accept(Request(message=message, transportInfo=self.transport))
        self.assertEqual(expected_response, response)


    def test_should_submit_if_parsing_is_successful(self):
        with patch.object(FormSubmissionFactory, 'get_form_submission') as get_form_submission_mock:
            get_form_submission_mock.return_value = self.form_submission_mock
            response = self.sms_player.accept(Request(message=self.message, transportInfo=self.transport))
            values = OrderedDict([(u'id', u'1'), (u'm', u'hello world'), ('l', None)])
            self.form_model_mock.is_valid.assert_called_once_with(values)
            self.form_submission_mock.save.assert_called_once_with(self.dbm)
            self.assertEqual('', response.datarecord_id)
            self.assertEqual([''], response.entity_type)

        #    TODO: Rewrite below test, skipping for now
    @SkipTest
    def test_should_submit_if_submission_by_registered_reporter(self):
        self.sms_player.accept(Request(message=self.message, transportInfo=self.transport))

        self.assertEqual(1, self.form_model_mock.submit.call_count)

        submission_request = self.form_model_mock.submit.call_args[0][0]
        self.assertEqual(self.reporter_mock, submission_request.reporter)


    def test_should_check_if_submission_by_unregistered_reporter(self):
        self.reporter_module.find_reporter_entity.side_effect = NumberNotRegisteredException("1234")
        with self.assertRaises(NumberNotRegisteredException):
            self.sms_player.accept(Request(message=self.message, transportInfo=self.transport))


    def test_should_not_submit_if_parsing_is_not_successful(self):
        with self.assertRaises(SMSParserInvalidFormatException):
            self.sms_player.accept(Request(message="invalid .format", transportInfo=self.transport))

        self.assertEqual(0, self.form_model_mock.is_valid.call_count)


    def test_should_not_parse_if_two_question_codes(self):
        transport = TransportInfo(transport="sms", source="1234", destination="5678")
        with self.assertRaises(MultipleSubmissionsForSameCodeException):
            self.sms_player.accept(Request(message="cli001 .na tester1 .na tester2", transportInfo=transport))

        self.assertEqual(0, self.form_model_mock.is_valid.call_count)


    def test_should_accept_ordered_sms_message(self):
        values = OrderedDict([('q1', u'question1_answer'), ('q2', u'question2_answer'), ('l', None)])
        request = Request(transportInfo=self.transport,
            message="questionnaire_code question1_answer question2_answer")
        order_sms_parser = OrderSMSParser(self.dbm)
        order_sms_parser._get_question_codes = Mock()
        order_sms_parser._get_question_codes.return_value = ['q1', 'q2'], self.form_model_mock
        with patch.object(FormSubmissionFactory, 'get_form_submission') as get_form_submission_mock:
            get_form_submission_mock.return_value = self.form_submission_mock
            response = SMSPlayer(self.dbm, self.loc_tree, order_sms_parser).accept(request)
            self.form_model_mock.is_valid.assert_called_once_with(values)
            self.form_submission_mock.save.assert_called_once_with(self.dbm)
            self.assertEqual('', response.datarecord_id)
            self.assertEqual([''], response.entity_type)

