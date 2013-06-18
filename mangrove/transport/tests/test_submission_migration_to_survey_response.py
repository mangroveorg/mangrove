from datetime import datetime
from pytz import UTC
from mangrove.datastore.tests.test_data import TestData
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.transport.contract.submission import Submission
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestMigration(MangroveTestCase):

    def test_copy_successful_submission_copied_to_survey_response(self):
        dictionary = {'Q1': 'test_submission_migration_to_survey_response', 'Q2': 'ans2'}
        submission_id = self.manager._save_document(
            SubmissionLogDocument(channel="transport", source=1234, destination=12345, form_code='form_code',
                values=dictionary, status=True, error_message="", data_record_id='sample_id', test=True,
                event_time=datetime.utcnow(), ))
        submission = Submission.get(self.manager, submission_id)
        survey_response = submission.create_survey_response(self.manager)

        self.assertIsNotNone(survey_response.uuid)
        self.assertEqual(dictionary, survey_response.values)
        self.assertEqual(submission._doc.submitted_on, survey_response._doc.submitted_on)
        self.assertEqual(submission.source, survey_response.origin)
        self.assertEqual(submission.channel, survey_response.channel)
        self.assertEqual(submission.destination, survey_response.destination)
        self.assertEqual(submission.form_code, survey_response.form_code)
        self.assertEqual(submission.form_model_revision, survey_response.form_model_revision)
        self.assertEqual(submission.status, survey_response.status)
        self.assertEqual(submission.is_void(), survey_response.is_void())
        self.assertEqual('', survey_response.errors)
        self.assertEqual(submission.test, survey_response.test)
        self.assertEqual(submission.event_time, survey_response.event_time)
        self.assertEqual(submission._doc.data_record_id, survey_response._doc.data_record_id)
        self.assertTrue(survey_response._doc.modified > submission._doc.modified)
        self.assertTrue(survey_response._doc.created > submission._doc.created)

    def test_copy_error_submission_copied_to_survey_response(self):
        dictionary = {'Q1': 'test_submission_migration_to_survey_response', 'Q2': 'ans2'}
        submission_id = self.manager._save_document(
            SubmissionLogDocument(channel="transport", source=1234, destination=12345, form_code='form_code',
                values=dictionary, status=False, error_message="answer for q1 was not a number",
                data_record_id='sample_id', test=True, event_time=datetime.utcnow(), ))
        submission = Submission.get(self.manager, submission_id)
        survey_response = submission.create_survey_response(self.manager)

        self.assertIsNotNone(survey_response.uuid)
        self.assertEqual(dictionary, survey_response.values)
        self.assertEqual(submission._doc.submitted_on, survey_response._doc.submitted_on)
        self.assertEqual(submission.source, survey_response.origin)
        self.assertEqual(submission.channel, survey_response.channel)
        self.assertEqual(submission.destination, survey_response.destination)
        self.assertEqual(submission.form_code, survey_response.form_code)
        self.assertEqual(submission.form_model_revision, survey_response.form_model_revision)
        self.assertEqual(submission.status, survey_response.status)
        self.assertEqual(submission.is_void(), survey_response.is_void())
        self.assertEqual("answer for q1 was not a number", survey_response.errors)
        self.assertEqual(submission.test, survey_response.test)
        self.assertEqual(submission.event_time, survey_response.event_time)
        self.assertEqual(submission._doc.data_record_id, survey_response._doc.data_record_id)
        self.assertTrue(survey_response._doc.modified > submission._doc.modified)
        self.assertTrue(survey_response._doc.created > submission._doc.created)

    def test_voided_submission_copied_to_survey_response(self):
        test_data = TestData(self.manager)
        data_record = [('meds', 20, test_data.dd_types['meds']),
                       ('doc', "aroj", test_data.dd_types['doctors']),
                       ('facility', 'clinic', test_data.dd_types['facility']),
                       ('opened_on', datetime(2011, 01, 02, tzinfo=UTC), test_data.dd_types['facility'])]
        data_record_id = test_data.entity1.add_data(data=data_record,
            event_time=datetime(2011, 01, 02, tzinfo=UTC),
            submission=dict(submission_id="123456"))

        dictionary = {'Q1': 'ans1', 'Q2': 'ans2'}
        submission_id = self.manager._save_document(
            SubmissionLogDocument(channel="transport", source=1234, destination=12345, form_code='form_code',
                values=dictionary, status=True, error_message='',
                data_record_id=data_record_id, test=True, event_time=datetime.utcnow(), ))

        submission = Submission.get(self.manager, submission_id)
        submission.void()

        survey_response = submission.create_survey_response(self.manager)

        self.assertIsNotNone(survey_response.uuid)
        self.assertEqual(dictionary, survey_response.values)
        self.assertEqual(submission._doc.submitted_on, survey_response._doc.submitted_on)
        self.assertEqual(submission.source, survey_response.origin)
        self.assertEqual(submission.channel, survey_response.channel)
        self.assertEqual(submission.destination, survey_response.destination)
        self.assertEqual(submission.form_code, survey_response.form_code)
        self.assertEqual(submission.form_model_revision, survey_response.form_model_revision)
        self.assertEqual(submission.status, survey_response.status)
        self.assertTrue(survey_response.is_void())
        self.assertEqual('', survey_response.errors)
        self.assertEqual(submission.test, survey_response.test)
        self.assertEqual(submission.event_time, survey_response.event_time)
        self.assertEqual(submission._doc.data_record_id, survey_response._doc.data_record_id)
        self.assertTrue(survey_response._doc.modified > submission._doc.modified)
        self.assertTrue(survey_response._doc.created > submission._doc.created)


