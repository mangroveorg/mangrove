from mangrove.form_model.field import TextField
from mangrove.transport import TransportInfo
from mangrove.transport.contract.submission import Submission
from mangrove.transport.player.player import Player
from mangrove.form_model.form_model import FormModel
from mangrove.utils.entity_builder import EntityBuilder
from mangrove.utils.form_model_builder import FormModelBuilder, create_default_ddtype
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestPlayer(MangroveTestCase):

    def test_should_save_the_correct_case_of_subject_short_code_in_submisson(self):
        self._build_entity()
        form_model = self._create_form_model()
        message = {'ID': 'SUBJECT_SHORT_CODE', 'Q1': 'words'}
        submission = Submission(self.manager, TransportInfo('sms', '8888567890', '123'), form_model.form_code, "revision", message)
        submission.save()

        response = Player(self.manager).submit(form_model, message, submission, None)

        self.assertTrue(response.success)
        self.assertEqual(submission.values[form_model.entity_question.code], 'subject_short_code')

    def test_should_save_revision_of_form_model_into_submission(self):
        self._build_entity()
        form_model = self._create_form_model()

        message = {'ID': 'SUBJECT_SHORT_CODE', 'Q1': 'words'}
        form_model = FormModel.get(self.manager, form_model.id)
        submission = Submission(self.manager, TransportInfo('sms', '8888567890', '123'), form_model.form_code, form_model.revision, message)
        submission_id = submission.save()

        saved_submission = Submission.get(self.manager, submission_id)
        self.assertIsNotNone(saved_submission.form_model_revision)
        self.assertEqual(saved_submission.form_model_revision, form_model.revision)

    def _build_entity(self):
        self.entity_type = ["subject"]
        EntityBuilder(self.manager, self.entity_type, "subject_short_code").build()

    def _create_form_model(self):
        ddtype = create_default_ddtype(self.manager)
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",entity_question_flag=True, ddtype=ddtype)
        question2 = TextField(name="question1_Name", code="Q1", label="What is your name",defaultValue="some default value", ddtype=ddtype)

        return FormModelBuilder(self.manager, self.entity_type).add_fields(question1, question2).build()

