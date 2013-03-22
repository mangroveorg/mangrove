# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from unittest.case import TestCase, SkipTest
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, NoQuestionsSubmittedException,\
    DataObjectNotFound, InactiveFormModelException

from mangrove.form_model.form_model import FormModel, FormSubmission
from mangrove.transport.facade import Channel

#TODO: Now that submission handler has been deleted, move these tests to the player.
@SkipTest
class TestSubmissionHandler(TestCase):

    def setUp(self):
        self.FORM_CODE = "QR1"
        self.VALUES = {"EID": "100", "Q1": "20"}

        self.dbm = Mock(spec=DatabaseManager)
        self.form_model_patcher = patch('mangrove.transport.submissions.get_form_model_by_code')
        self.form_submission_entity_patcher = patch('mangrove.form_model.form_model.entity')

        self.get_form_model_mock = self.form_model_patcher.start()
        self.form_submission_entity_module = self.form_submission_entity_patcher.start()
        self.SUBMISSION_ID = "SUBMISSION_ID"

        self.form_model_mock = Mock(spec=FormModel)
        self.form_model_mock.is_registration_form.return_value = False
        self.form_model_mock.entity_defaults_to_reporter.return_value = False
        self.form_model_mock.is_inactive.return_value = False
        self.form_model_mock.is_in_test_mode.return_value = False
        self.ENTITY_TYPE = ["entity_type"]
        self.form_model_mock.entity_type = self.ENTITY_TYPE
        entity_question = Mock()
        entity_question.code = "eid"
        self.form_model_mock.entity_question = entity_question
        self.get_form_model_mock.return_value = self.form_model_mock
        self.sms = Channel.SMS

        reporter = Mock(spec=Entity)
        reporter.short_code.return_value = "REP1"
        self.submission_request = None

    def tearDown(self):
        self.form_model_patcher.stop()
        self.form_submission_entity_patcher.stop()

    def _valid_form_submission(self):
        return FormSubmission(self.form_model_mock, {'eid': 'CID001', "location": "Pune"})

    def _valid_form_submission_unicode(self):
        return FormSubmission(self.form_model_mock, {'eid': u'Āgra', "location": "Agra"})

    def _invalid_form_submission_unicode(self):
        return FormSubmission(self.form_model_mock, {}, {"field": u"Āgra"})


    def _valid_form_submission_with_choices(self):
        return FormSubmission(self.form_model_mock,
                {'eid': 'CID001', "location": "Pune", "favourite_colour": ['red']})

    def _empty_form_submission(self):
        return FormSubmission(self.form_model_mock, {'eid': 'CID001'})


    def _invalid_form_submission(self):
        return FormSubmission(self.form_model_mock, {}, {"field": "Invalid"})


    @SkipTest
    def test_should_return_true_if_valid_form_submission(self):
        self.form_model_mock.validate_submission.return_value = self._valid_form_submission()

        response = self.submission_handler.accept(self.submission_request)

        self.assertTrue(response.success)
        self.assertEqual({}, response.errors)
        self.assertFalse(response.is_registration)


    @SkipTest
    def test_should_save_data_record_if_valid_form_submission(self):
        self.form_model_mock.validate_submission.return_value = self._valid_form_submission()

        self.submission_handler.accept(self.submission_request)

        self.assertTrue(self.form_submission_entity_module.get_by_short_code.called)


    @SkipTest
    def test_should_not_save_data_record_if_in_valid_form_submission(self):
        self.form_model_mock.validate_submission.return_value = self._invalid_form_submission()

        response = self.submission_handler.accept(self.submission_request)

        self.assertEqual({"field": "Invalid"}, response.errors)
        self.assertFalse(response.success)
        self.assertFalse(response.is_registration)

    def test_should_not_save_data_record_if_no_valid_questions_present(self):
        self.form_model_mock.validate_submission.side_effect = NoQuestionsSubmittedException()
        with self.assertRaises(NoQuestionsSubmittedException):
            self.submission_handler.accept(self.submission_request)


    @SkipTest
    def test_should_fail_submission_if_invalid_form_code(self):
        self.get_form_model_mock.side_effect = FormModelDoesNotExistsException("INVALID_CODE")

        with self.assertRaises(FormModelDoesNotExistsException):
            self.submission_handler.accept(self.submission_request)


    @SkipTest
    def test_should_fail_submission_if_invalid_short_code(self):
        form_submission = self._valid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission

        self.form_submission_entity_module.get_by_short_code.side_effect = DataObjectNotFound("Entity", 'id',
                                                                                              'short_code')

        with self.assertRaises(DataObjectNotFound):
            self.submission_handler.accept(self.submission_request)


    @SkipTest
    def test_should_register_entity_if_form_submission_valid(self):
        self.form_model_mock.validate_submission.return_value = self._valid_form_submission()
        self.form_model_mock.is_registration_form.return_value = True

        response = self.submission_handler.accept(self.submission_request)

        self.assertTrue(response.success)
        self.assertEqual({}, response.errors)
        self.assertEqual("cid001", response.short_code)
        self.assertTrue(response.is_registration)
        self.form_submission_entity_module.create_entity.assert_called_once_with(dbm=self.dbm, entity_type=self
        .ENTITY_TYPE,
                                                                                 location=None,
                                                                                 short_code="cid001", geometry=None)
    @SkipTest
    def test_should_not_register_entity_if_form_submission_invalid(self):
        form_submission = self._invalid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission
        self.form_model_mock.is_registration_form.return_value = True

        response = self.submission_handler.accept(self.submission_request)

        self.assertFalse(response.success)
        self.assertEqual({"field": "Invalid"}, response.errors)
        self.assertTrue(response.is_registration)
        self.assertFalse(self.form_submission_entity_module.create_entity.called)


    @SkipTest
    def test_should_return_expanded_response(self):
        form_submission = self._valid_form_submission_with_choices()
        self.form_model_mock.validate_submission.return_value = form_submission

        response = self.submission_handler.accept(self.submission_request)

        expected_message = form_submission.cleaned_data
        self.assertEquals(expected_message, response.processed_data)


    @SkipTest
    def test_should_accept_unicodes_for_valid_submission(self):
        form_submission = self._valid_form_submission_unicode()
        self.form_model_mock.validate_submission.return_value = form_submission

        response = self.submission_handler.accept(self.submission_request)

        self.assertTrue(response.success)
        self.assertEqual({}, response.errors)


    @SkipTest
    def test_should_accept_unicodes_for_invalid_submission(self):
        form_submission = self._invalid_form_submission_unicode()
        self.form_model_mock.validate_submission.return_value = form_submission

        response = self.submission_handler.accept(self.submission_request)

        self.assertFalse(response.success)
        self.assertEqual({'field': u'Āgra'}, response.errors)


    @SkipTest
    def test_should_raise_inactive_form_model_exception(self):
        self.form_model_mock.is_inactive.return_value = True
        with self.assertRaises(InactiveFormModelException):
            self.submission_handler.accept(self.submission_request)


    @SkipTest
    def test_should_log_submissions_in_test_mode(self):
        self.form_model_mock.is_in_test_mode.return_value = True
        self.form_model_mock.is_inactive.return_value = False
        form_submission = self._valid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission

        response = self.submission_handler.accept(self.submission_request)

        self.assertTrue(response.success)
        self.assertIsNotNone(response.datarecord_id)
        self.assertIsNotNone(response.submission_id)
