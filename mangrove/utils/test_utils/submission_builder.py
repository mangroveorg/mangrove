from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.form_model.form_model import FORM_CODE
from mangrove.transport.submissions import Submission

class SubmissionBuilder(object):
    def __init__(self, manager):
        self.manager = manager

    def build_four_submissions(self):
        return self.build_two_successful_submissions() + self.build_two_error_submission()

    def build_two_successful_submissions(self):
        doc_id1 = self.manager._save_document(
            SubmissionLogDocument(channel="transport", source=1234, destination=12345, form_code=FORM_CODE,
                values={'Q1': 'ans1', 'Q2': 'ans2'}, status=True, error_message=""))
        doc_id2 = self.manager._save_document(
            SubmissionLogDocument(channel="transport", source=1234, destination=12345, form_code=FORM_CODE,
                values={'Q1': 'ans12', 'Q2': 'ans22'}, status=True, error_message=""))

        return [Submission.get(self.manager, id) for id in [doc_id1, doc_id2]]

    def build_two_error_submission(self):
        doc_id3 = self.manager._save_document(
            SubmissionLogDocument(channel="transport", source=1234, destination=12345, form_code=FORM_CODE,
                values={'Q3': 'ans12', 'Q4': 'ans22'}, status=False, error_message=""))
        doc_id4 = self.manager._save_document(
            SubmissionLogDocument(channel="transport", source=1234, destination=12345, form_code="def",
                values={'defQ1': 'defans12', 'defQ2': 'defans22'}, status=False, error_message=""))

        return [Submission.get(self.manager, id) for id in [doc_id3, doc_id4]]

