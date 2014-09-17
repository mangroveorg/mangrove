from mangrove.datastore.documents import SurveyResponseDocument
from mangrove.form_model.form_model import FORM_MODEL_ID
from mangrove.transport.contract.survey_response import SurveyResponse

#TODO: Make all Tests use the build method
class TestSurveyResponseBuilder(object):
    def __init__(self, manager, channel='web', destination=12345, form_model_id=FORM_MODEL_ID, values=None,
                 status=True, error_message=''):
        self.manager = manager
        self.channel = channel
        self.destination = destination
        self.form_model_id = form_model_id
        self.values = values
        self.status = status
        self.error_message = error_message


    def build(self, owner_id):
        survey_response_id = self.manager._save_document(
            SurveyResponseDocument(channel=self.channel,
                                   destination=self.destination, values=self.values, status=self.status,
                                   error_message=self.error_message,
                                   form_model_id=self.form_model_id, owner_uid=owner_id))
        return SurveyResponse.get(self.manager, survey_response_id)

    def build_four_survey_responses(self):
        return self.build_two_successful_survey_responses() + self.build_two_error_survey_responses()

    def build_two_successful_survey_responses(self):
        doc_id1 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", destination=12345, form_model_id=FORM_MODEL_ID,
                                   values={'Q1': 'ans1', 'Q2': 'ans2'}, status=True, error_message=""))
        doc_id2 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", destination=12345, form_model_id=FORM_MODEL_ID,
                                   values={'Q1': 'ans12', 'Q2': 'ans22'}, status=True, error_message=""))

        return [SurveyResponse.get(self.manager, id) for id in [doc_id1, doc_id2]]

    def build_two_error_survey_responses(self):
        doc_id3 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", destination=12345, form_model_id=FORM_MODEL_ID,
                                   values={'Q3': 'ans12', 'Q4': 'ans22'}, status=False, error_message=""))
        doc_id4 = self.manager._save_document(
            SurveyResponseDocument(channel="transport", destination=12345, form_model_id="def",
                                   values={'defQ1': 'defans12', 'defQ2': 'defans22'}, status=False, error_message=""))

        return [SurveyResponse.get(self.manager, id) for id in [doc_id3, doc_id4]]

