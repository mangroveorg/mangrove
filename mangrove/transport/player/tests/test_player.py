from mangrove.datastore.datadict import DataDictType
from mangrove.datastore.entity_type import define_type
from mangrove.form_model.field import TextField
from mangrove.form_model.validation import TextLengthConstraint, RegexConstraint
from mangrove.transport import TransportInfo
from mangrove.transport.submissions import Submission
from mangrove.transport.player.player import Player
from mangrove.form_model.form_model import FormModel
from mangrove.utils.entity_builder import EntityBuilder
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
        self._create_form_model()

        message = {'ID': 'SUBJECT_SHORT_CODE', 'Q1': 'words'}
        form_model = FormModel.get(self.manager, self.form_model_id)
        submission = Submission(self.manager, TransportInfo('sms', '8888567890', '123'), form_model.form_code, form_model.revision, message)
        submission_id = submission.save()

        saved_submission = Submission.get(self.manager, submission_id)
        self.assertIsNotNone(saved_submission.form_model_revision)
        self.assertEqual(saved_submission.form_model_revision, form_model.revision)

    def _build_entity(self):
        self.entity_type = ["subject"]
        define_type(self.manager, self.entity_type)
        EntityBuilder(self.manager, self.entity_type, "subject_short_code").build()

    def _create_form_model(self):
        self._create_default_ddtype()
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
            entity_question_flag=True, ddtype=self.default_ddtype)
        question2 = TextField(name="question1_Name", code="Q1", label="What is your name",
            defaultValue="some default value", constraints=[TextLengthConstraint(5, 10), RegexConstraint("\w+")],
            ddtype=self.default_ddtype)
        self.form_model = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
            form_code="form_code", type='survey', fields=[question1, question2])
        self.form_model_id = self.form_model.save()
        return self.form_model

    def _create_default_ddtype(self):
        self.default_ddtype = DataDictType(self.manager, name='default dd type', slug='slug_name',
            primitive_type='text')
        self.default_ddtype.save()

