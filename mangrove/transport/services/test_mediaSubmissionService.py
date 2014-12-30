from unittest import TestCase
from mock import Mock, patch, PropertyMock
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.field import PhotoField, TextField, FieldSet
from mangrove.form_model.form_model import FormModel
from mangrove.transport.services.MediaSubmissionService import MediaSubmissionService


class TestMediaSubmissionService(TestCase):
    def setUp(self):
        dbm = Mock(spec=DatabaseManager)
        self.image = Mock()
        self.image.size = 1000000
        media = {"image.png": self.image}
        form_code = "form_code"
        self.form_model = Mock(spec=FormModel)
        self.form_model.form_code = PropertyMock(return_value=form_code)
        self.form_model.is_media_type_fields_present = PropertyMock(return_value=True)
        with patch("mangrove.transport.services.MediaSubmissionService.get_form_model_by_code") as get_form_model:
            get_form_model.return_value = self.form_model
            self.media_submission_service = MediaSubmissionService(dbm, media, form_code)

    def test__get_media_fields_and_update_values(self):
        values = [{u'image': u'image.png'}]
        counter = count_generator()
        photo_field = PhotoField('image', 'image', 'image')
        with patch(
                "mangrove.transport.services.MediaSubmissionService.MediaSubmissionService._create_document") as document_created:
            media_files = self.media_submission_service._get_media_fields_and_update_values([photo_field], values,
                                                                                            counter)
            expected_files = {"1-image.png": self.image}
            self.assertDictEqual(expected_files, media_files)

    def test__get_media_fields_in_a_group_and_update_values(self):
        values = [{"group": [{"image": "image.png", "name": "something"}]}]
        counter = count_generator()
        field1 = PhotoField('image', 'image', 'image')
        field2 = TextField(name='name', code='name', label='wat is ur name')
        field_set = FieldSet('group', 'group', 'group', field_set=[field1, field2])
        with patch(
                "mangrove.transport.services.MediaSubmissionService.MediaSubmissionService._create_document") as document_created:
            media_files = self.media_submission_service._get_media_fields_and_update_values([field_set], values,
                                                                                            counter)
            expected_files = {"1-image.png": self.image}
            self.assertDictEqual(expected_files, media_files)

    def test__get_media_fields_in_a_repeat_and_update_values(self):
        values = [{"group": [{"image": "image.png", "name": "something"}, {"image": "image.png", "name": "something2"},
                             {"image": "image.png", "name": "something3"}]}]
        counter = count_generator()
        field1 = PhotoField('image', 'image', 'image')
        field2 = TextField(name='name', code='name', label='wat is ur name')
        field_set = FieldSet('group', 'group', 'group', field_set=[field1, field2])
        with patch(
                "mangrove.transport.services.MediaSubmissionService.MediaSubmissionService._create_document") as document_created:
            media_files = self.media_submission_service._get_media_fields_and_update_values([field_set], values,
                                                                                            counter)
            expected_files = {"1-image.png": self.image, "2-image.png": self.image, "3-image.png": self.image}
            self.assertDictEqual(expected_files, media_files)


def count_generator():
    count = 0
    while True:
        count += 1
        yield count