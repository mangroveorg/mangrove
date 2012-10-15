from collections import OrderedDict
from unittest import TestCase
from mangrove.transport.submissions import Submission
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.transport.player.player import Player
from mock import Mock, patch
from mangrove.form_model.form_model import FormModel, FormSubmission, DataFormSubmission

class TestPlayer(TestCase):
    def test_should_use_submission_id_instead_of_submission(self):
        dbm = Mock(spec=DatabaseManager)
        message = {'q1': 'CAPITAL'}

        submission = Mock(spec=Submission)
        submission.values = message

        form_model = Mock(spec=FormModel)
        form_model.entity_question.code = 'q1'
        form_model.is_inactive.return_value = False
        form_model.validate_submission.return_value = OrderedDict(submission.values), None
        form_model.is_registration_form.return_value = False

        with patch.object(FormSubmission, "get_entity_type") as get_entity_type:
            with patch.object(DataFormSubmission, "create_entity") as create_entity:
                create_entity.return_value = Mock(spec=Entity)
                get_entity_type.return_value = ['subject']
                response = Player(dbm).submit(form_model, message, submission, None)

                self.assertTrue(response.success)
                self.assertEqual(submission.values[form_model.entity_question.code], 'capital')
