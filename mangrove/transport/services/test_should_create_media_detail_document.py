from mangrove.form_model.form_model import FormModel
from mangrove.transport.services.MediaSubmissionService import MediaSubmissionService
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase


class TestCreateMediaDocument(MangroveTestCase):
    def test_should_create_media_detail_document(self):
        form_model = FormModel(self.manager, "name", form_code="code", fields=[])
        form_model.save()
        media_submission_service = MediaSubmissionService(self.manager, {}, "code")
        count = next(media_submission_service._get_count(form_model.id))
        self.assertEquals(1, count)
        media_submission_service.create_media_details_document(1000000, "new_image")
        count = next(media_submission_service._get_count(form_model.id))
        self.assertEquals(2, count)