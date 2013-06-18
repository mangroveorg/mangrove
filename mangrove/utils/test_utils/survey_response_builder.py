from mangrove.datastore.documents import  SurveyResponseDocument
from mangrove.form_model.form_model import FORM_CODE
from mangrove.transport.contract.submission import Submission
from mangrove.transport.contract.survey_response import SurveyResponse

#TODO: Make all Tests use the build method
class TestSurveyResponseBuilder(object):
    def __init__(self, manager, channel='web', source=1234, destination=12345, form_code=FORM_CODE, values=None,
                 status=True, error_message=''):
        self.manager = manager
        self.channel = channel
        self.source = source
        self.destination = destination
        self.form_code = form_code
        self.values = values
        self.status = status
        self.error_message = error_message


    def build(self):
        survey_response_id = self.manager._save_document(
            SurveyResponseDocument(origin=self.source, channel=self.channel,
                destination=self.destination, values=self.values, status=self.status, error_message=self.error_message,
                form_code=self.form_code))
        return SurveyResponse.get(self.manager, survey_response_id)

    def build_four_survey_responses(self):
        return self.build_two_successful_survey_responses() + self.build_two_error_survey_responses()

    def build_two_successful_survey_responses(self):
        doc_id1 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", origin=1234, destination=12345, form_code=FORM_CODE,
                values={'Q1': 'ans1', 'Q2': 'ans2'}, status=True, error_message=""))
        doc_id2 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", origin=1234, destination=12345, form_code=FORM_CODE,
                values={'Q1': 'ans12', 'Q2': 'ans22'}, status=True, error_message=""))

        return [Submission.get(self.manager, id) for id in [doc_id1, doc_id2]]

    def build_two_error_survey_responses(self):
        doc_id3 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", origin=1234, destination=12345, form_code=FORM_CODE,
                values={'Q3': 'ans12', 'Q4': 'ans22'}, status=False, error_message=""))
        doc_id4 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", origin=1234, destination=12345, form_code="def",
                values={'defQ1': 'defans12', 'defQ2': 'defans22'}, status=False, error_message=""))

        return [Submission.get(self.manager, id) for id in [doc_id3, doc_id4]]

