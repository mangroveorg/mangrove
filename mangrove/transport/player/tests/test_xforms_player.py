from mangrove.datastore.tests.test_data import TestData
from mangrove.transport.player.new_players import XFormPlayerV2
from mangrove.transport.contract.transport_info import TransportInfo
from mangrove.transport.contract.request import Request
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

ENTITY_TYPE = "some_entity"

class TestXformPlayerIT(MangroveTestCase):
    xform_message = """<?xml version='1.0' ?>
<data id="xxx">
    <id>1</id>
    <Q1>Tom</Q1>
    <Q2>100</Q2>
    <Q3>a</Q3>
    <form_code>CL1</form_code>
</data>
"""
    def setUp(self):
        super(TestXformPlayerIT, self).setUp()
        self.org_id = 'SLX364903'
        self.player = XFormPlayerV2(self.manager)
        message = self.xform_message
        self.transport = TransportInfo(transport="xform", source="mail@domain.com", destination="5678")
        self.request = Request(message=message, transportInfo=self.transport)
        TestData(self.manager)

    def test_create_survey_response(self):
        response = self.player.add_survey_response(self.request)
        self.assertEqual(response.success, True)
        self.assertIsNotNone(response.survey_response_id)
        self.assertIsNotNone(response.submission_id)

    def tearDown(self):
        MangroveTestCase.tearDown(self)