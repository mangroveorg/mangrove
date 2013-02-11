from collections import OrderedDict
import unittest
from couchdb.mapping import Document
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType
from mangrove.datastore.documents import FormModelDocument, DataRecordDocument, EntityDocument, DocumentBase
from mangrove.datastore.entity import DataRecord
from mangrove.form_model.form_model import EntityRegistrationFormSubmission
from mangrove.form_model.form_model import GlobalRegistrationFormSubmission, GLOBAL_REGISTRATION_FORM_ENTITY_TYPE
from mangrove.form_model.form_model import DataFormSubmission, FormSubmissionFactory, FormModel
from mangrove.transport.submissions import Submission

class TestFormSubmissionFactory(unittest.TestCase):
    def test_should_give_data_form_submission(self):
        mocked_form_model = Mock(spec=FormModel)
        mocked_form_model.is_registration_form.return_value = False
        mocked_form_model.entity_type = "clinic"
        form_submission = FormSubmissionFactory().get_form_submission(mocked_form_model, OrderedDict(), None)
        self.assertEqual(type(form_submission), DataFormSubmission)

    def test_should_give_global_registration_form_submission(self):
        mocked_form_model = Mock(spec=FormModel)
        mocked_form_model.is_registration_form.return_value = True
        mocked_form_model.entity_type = GLOBAL_REGISTRATION_FORM_ENTITY_TYPE
        form_submission = FormSubmissionFactory().get_form_submission(mocked_form_model, OrderedDict(), None)
        self.assertEqual(type(form_submission), GlobalRegistrationFormSubmission)

    def test_should_give_entity_specific_registration_form_submission(self):
        mocked_form_model = Mock(spec=FormModel)
        mocked_form_model.is_registration_form.return_value = True
        mocked_form_model.entity_type = "clinic"
        form_submission = FormSubmissionFactory().get_form_submission(mocked_form_model, OrderedDict(), None)
        self.assertEqual(type(form_submission), EntityRegistrationFormSubmission)


    def test_should_update_existing_data_records(self):
        mocked_form_model = Mock(spec=FormModel)
        mocked_form_model.is_registration_form.return_value = False
        mocked_form_model.entity_type = "clinic"
        form_submission = FormSubmissionFactory().get_form_submission(mocked_form_model, OrderedDict(), None)

        form_submission._values.insert(0,(u'What are symptoms?', ['High Fever'],Mock(DataDictType)))

        mock_dbm = Mock(DatabaseManager)
        data_record = DataRecord(mock_dbm)
        data_record._doc = DataRecordDocument(entity_doc=EntityDocument())
        data_record._doc.entity['data'] = {u'What are symptoms?': {'value': ['Dry cough', 'Memory loss']}}

        data_record_id = 'abcdefgh1234jklmnop'
        submission = DocumentBase(document_type=(Mock(Document)))
        submission._data['data_record_id'] = data_record_id

        with patch('mangrove.datastore.database.DatabaseManager._load_document') as load_document:
            with patch('mangrove.datastore.database.DataObject.get') as get_data_record:
                load_document.return_value = data_record_id
                get_data_record.return_value = data_record

                form_submission.update_existing_data_records(mock_dbm,'8765gjngtbhjmk4567hloub')

        data_record.save().assert_called_once()
