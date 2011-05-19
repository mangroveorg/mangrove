# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.transport.submissions import Response


class TestResponse(unittest.TestCase):
    def test_should_generate_response_with_registration_id(self):
        response = Response(reporters=[{"first_name": "asif"}], success=True, errors=None, submission_id=None,
                            datarecord_id=123, include_id_in_message=True)
        self.assertEqual(response.message, "Thank You asif for your submission. The record id is - 123")
        self.assertEqual(response.datarecord_id, 123)

    def test_should_generate_response_without_registration_id(self):
        response = Response(reporters=[{"first_name": "asif"}], success=True, errors=None, submission_id=None,
                            datarecord_id=123)
        self.assertEqual(response.message, "Thank You asif for your submission.")
        self.assertEqual(response.datarecord_id, 123)
