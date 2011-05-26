# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.form_model.form_model import NAME_FIELD
from mangrove.transport.submissions import Response


class TestResponse(unittest.TestCase):
    def test_should_generate_response_with_additional_text(self):
        response = Response(reporters=[{NAME_FIELD: "asif"}], success=True, errors=None, submission_id=None,
                            datarecord_id=123, additional_text="The record id is - 123")
        self.assertEqual(response.message, "Thank You asif for your submission. The record id is - 123")
        self.assertEqual(response.datarecord_id, 123)

    def test_should_generate_response_without_additional_text(self):
        response = Response(reporters=[{NAME_FIELD: "asif"}], success=True, errors=None, submission_id=None,
                            datarecord_id=123)
        self.assertEqual(response.message, "Thank You asif for your submission.")
        self.assertEqual(response.datarecord_id, 123)

    def test_should_generate_response_with_error_data(self):
        response = Response(reporters=[{NAME_FIELD: "asif"}], success=False, errors=None, error_data = [('q1', '20'),('q2',)], submission_id=None,
                            datarecord_id=123)
        expected_message = "Error. Invalid Submission. Refer to printed Questionnaire. Resend the question ID and answer for q1, q2"
        self.assertEqual(expected_message, response.message)

    def test_should_generate_response_without_error_data(self):
        error_message = "Invalid registration or something like that"
        response = Response(reporters=[{NAME_FIELD: "asif"}], success=False, errors=[error_message], submission_id=None,
                            datarecord_id=123)
        expected_message = error_message
        self.assertEqual(expected_message, response.message)
