# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.errors.MangroveException import FormModelDoesNotExistsException, NoQuestionsSubmittedException, DataObjectNotFound
from mangrove.form_model.form_model import FormModel, FormSubmission
from mangrove.transport.player.player import   Channel
from mangrove.transport.submissions import SubmissionHandler, SubmissionLogger, SubmissionRequest


class TestSubmissions(TestCase):
    ENTITY_TYPE = ["EntityType"]

    def setUp(self):
        self.FORM_CODE = "QR1"
        self.VALUES = {"EID": "100", "Q1": "20"}

        self.dbm = Mock(spec=DatabaseManager)
        self.form_model_patcher = patch('mangrove.transport.submissions.get_form_model_by_code')
        self.form_submission_entity_patcher = patch('mangrove.form_model.form_model.entity')
        self.entity_patcher = patch('mangrove.transport.submissions.entity')
        self.SubmissionLogger_class_patcher = patch('mangrove.transport.submissions.SubmissionLogger', )

        self.get_form_model_mock = self.form_model_patcher.start()
        self.entity_module = self.entity_patcher.start()
        self.form_submission_entity_module = self.form_submission_entity_patcher.start()
        self.SubmissionLogger_mock_class = self.SubmissionLogger_class_patcher.start()
        self.submissionLogger = Mock(spec=SubmissionLogger)
        self.SubmissionLogger_mock_class.return_value = self.submissionLogger
        self.SUBMISSION_ID = "SUBMISSION_ID"
        self.submissionLogger.create_submission_log.return_value = self.SUBMISSION_ID

        self.form_model_mock = Mock(spec=FormModel)
        self.form_model_mock._is_registration_form.return_value = False
        self.form_model_mock.entity_defaults_to_reporter.return_value = False
        self.get_form_model_mock.return_value = self.form_model_mock
        self.sms = Channel.SMS

        self.submission_request = SubmissionRequest(form_code=self.FORM_CODE, submission=self.VALUES, transport=self.sms
                                                    , source="1234", destination="5678")
        self.submission_handler = SubmissionHandler(self.dbm)

    def tearDown(self):
        self.form_model_patcher.stop()
        self.form_submission_entity_patcher.stop()
        self.entity_patcher.stop()

    def _valid_form_submission(self):
        return FormSubmission(self.form_model_mock, {'What is associated entity?': 'CID001', "location": "Pune"}, "1",
                              True, {}, "entity_type", data={})

    def _valid_form_submission_unicode(self):
        return FormSubmission(self.form_model_mock, {'What is associated entity?': u'Āgra', "location": "Agra"}, "1",
                              True, {}, "entity_type", data={})

    def _invalid_form_submission_unicode(self):
        return FormSubmission(self.form_model_mock, {}, "1", False, {"field": u"Āgra"}, self.ENTITY_TYPE, data={})


    def _valid_form_submission_with_choices(self):
        return FormSubmission(self.form_model_mock,
                {'What is associated entity?': 'CID001', "location": "Pune", "favourite_colour": ['red']}, "1",
                              True, {}, self.ENTITY_TYPE, data={})

    def _empty_form_submission(self):
        return FormSubmission(self.form_model_mock, {'What is associated entity?': 'CID001'}, "1", True, {},
                              self.ENTITY_TYPE, data={})


    def _invalid_form_submission(self):
        return FormSubmission(self.form_model_mock, {}, "1", False, {"field": "Invalid"}, self.ENTITY_TYPE, data={})

    def test_should_return_true_if_valid_form_submission(self):
        self.form_model_mock.validate_submission.return_value = self._valid_form_submission()

        response = self.submission_handler.accept(self.submission_request)

        self.assertTrue(response.success)
        self.assertEqual({}, response.errors)


    def test_should_save_data_record_if_valid_form_submission(self):
        self.form_model_mock.validate_submission.return_value = self._valid_form_submission()

        response = self.submission_handler.accept(self.submission_request)

        self.assertTrue(self.form_submission_entity_module.get_by_short_code.called)


    def test_should_not_save_data_record_if_in_valid_form_submission(self):
        self.form_model_mock.validate_submission.return_value = self._invalid_form_submission()

        response = self.submission_handler.accept(self.submission_request)

        self.assertFalse(self.entity_module.add_data.called)
        self.assertEqual({"field": "Invalid"}, response.errors)
        self.assertFalse(response.success)

    def test_should_not_save_data_record_if_no_valid_questions_present(self):
        self.form_model_mock.validate_submission.return_value = self._empty_form_submission()
        with self.assertRaises(NoQuestionsSubmittedException):
            response = self.submission_handler.accept(self.submission_request)


    def test_should_create_new_submission_log(self):
        form_submission = self._valid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission

        response = self.submission_handler.accept(self.submission_request)

        self.assertTrue(self.submissionLogger.create_submission_log.called)


    def test_should_update_submission_log_on_success(self):
        form_submission = self._valid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission

        response = self.submission_handler.accept(self.submission_request)

        self.submissionLogger.update_submission_log.assert_called_once_with(submission_id=self.SUBMISSION_ID,
                                                                            status=True, errors=[],
                                                                            data_record_id=response.datarecord_id)


    def test_should_update_submission_log_on_failure(self):
        form_submission = self._invalid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission

        response = self.submission_handler.accept(self.submission_request)

        self.submissionLogger.update_submission_log.assert_called_once_with(submission_id=self.SUBMISSION_ID,
                                                                            status=False,
                                                                            errors=form_submission.errors.values())

    def test_should_fail_submission_if_invalid_form_code(self):
        dbm = Mock(spec=DatabaseManager)
        self.get_form_model_mock.side_effect = FormModelDoesNotExistsException("INVALID_CODE")

        with self.assertRaises(FormModelDoesNotExistsException):
            response = self.submission_handler.accept(self.submission_request)

    def test_should_fail_submission_if_invalid_short_code(self):
        form_submission = self._valid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission

        self.form_submission_entity_module.get_by_short_code.side_effect = DataObjectNotFound("Entity", 'id',
                                                                                              'short_code')

        with self.assertRaises(DataObjectNotFound):
            self.submission_handler.accept(self.submission_request)

    def test_should_register_entity_if_form_submission_valid(self):
        self.form_model_mock.validate_submission.return_value = self._valid_form_submission()
        self.form_model_mock._is_registration_form.return_value = True

        response = self.submission_handler.accept(self.submission_request)

        self.assertTrue(response.success)
        self.assertEqual({}, response.errors)
        self.form_submission_entity_module.create_entity.assert_called_once_with(dbm=self.dbm, entity_type="entity_type"
                                                                                 ,
                                                                                 location=None,
                                                                                 short_code="1", geometry=None)
        self.submissionLogger.update_submission_log.assert_called_once_with(submission_id=self.SUBMISSION_ID,
                                                                            status=True, errors=[],
                                                                            data_record_id=response.datarecord_id)


    def test_should_not_register_entity_if_form_submission_invalid(self):
        form_submission = self._invalid_form_submission()
        self.form_model_mock.validate_submission.return_value = form_submission
        self.form_model_mock._is_registration_form.return_value = True

        response = self.submission_handler.accept(self.submission_request)

        self.assertFalse(response.success)
        self.assertEqual({"field": "Invalid"}, response.errors)
        self.assertFalse(self.form_submission_entity_module.create_entity.called)
        self.submissionLogger.update_submission_log.assert_called_once_with(submission_id=self.SUBMISSION_ID,
                                                                            status=False,
                                                                            errors=form_submission.errors.values())

    def test_should_return_expanded_response(self):
        form_submission = self._valid_form_submission_with_choices()
        self.form_model_mock.validate_submission.return_value = form_submission

        response = self.submission_handler.accept(self.submission_request)

        expected_message = form_submission.cleaned_data
        self.assertEquals(expected_message, response.processed_data)

    def test_should_get_reporter_by_from_number_if_activity_report(self):
        form_submission = self._valid_form_submission()
        reporter_patcher = patch('mangrove.transport.submissions.reporter')
        reporter_module = reporter_patcher.start()
        self.form_model_mock.validate_submission.return_value = form_submission
        self.form_model_mock._is_registration_form.return_value = False
        self.form_model_mock.entity_defaults_to_reporter.return_value = True

        response = self.submission_handler.accept(self.submission_request)

        self.assertTrue(response.success)
        self.assertTrue(reporter_module.get_short_code_from_reporter_number.called)
        reporter_patcher.stop()

    def test_should_accept_unicodes_for_valid_submission(self):
        form_submission = self._valid_form_submission_unicode()
        self.form_model_mock.validate_submission.return_value = form_submission

        response = self.submission_handler.accept(self.submission_request)

        self.assertTrue(response.success)
        self.assertEqual({}, response.errors)

    def test_should_accept_unicodes_for_invalid_submission(self):
        form_submission = self._invalid_form_submission_unicode()
        self.form_model_mock.validate_submission.return_value = form_submission

        response = self.submission_handler.accept(self.submission_request)

        self.assertFalse(response.success)
        self.assertEqual({'field': u'Āgra'}, response.errors)