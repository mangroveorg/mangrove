from collections import OrderedDict
from mangrove.form_model.field import TextField
from mangrove.form_model.validation import TextLengthConstraint, RegexConstraint
from mangrove.transport import TransportInfo
from mangrove.transport.submissions import Submission
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.transport.player.player import Player
from mock import Mock, patch
from mangrove.form_model.form_model import FormModel, FormSubmission, DataFormSubmission
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase

class TestPlayer(MangroveTestCase):

    def test_should_save_the_correct_case_of_subject_short_code_in_submisson(self):
        form_model = self._create_form_model()

        Submission(self.manager, TransportInfo('sms', '8888567890', '123'), form_model.form_code,{'q1': 'Q1_VALUE'}).save()


        with patch.object(FormSubmission, "get_entity_type") as get_entity_type:
            with patch.object(DataFormSubmission, "create_entity") as create_entity:
                create_entity.return_value = Mock(spec=Entity)
                get_entity_type.return_value = ['subject']
                response = Player(dbm).submit(form_model, message, submission, None)

                self.assertTrue(response.success)
                self.assertEqual(submission.values[form_model.entity_question.code], 'capital')


    def test_should_save_revision_of_form_model_into_submission(self):
        pass


    def _create_form_model(self):
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
            entity_question_flag=True, ddtype=self.default_ddtype)
        question2 = TextField(name="question1_Name", code="Q1", label="What is your name",
            defaultValue="some default value", constraints=[TextLengthConstraint(5, 10), RegexConstraint("\w+")],
            ddtype=self.default_ddtype)
        self.form_model = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
            form_code="form_code", type='survey', fields=[question1, question2])
        self.form_model__id = self.form_model.save()
        return self.form_model

