from mangrove.form_model.field import field_attributes
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.form_model.media import Media

ONE_MB = 1000000


class MediaSubmissionService():
    def __init__(self, dbm, logger, media, form_code):
        self.dbm = dbm
        self.logger = logger
        self.media = media
        self.form_model = get_form_model_by_code(self.dbm, form_code)

    def create_media_documents(self, values):
        fields = self.form_model.fields
        counter = self._get_count(self.form_model.id)
        return self._get_media_fields_and_update_values(fields, [values], counter)

    def _get_count(self, form_model_id):
        while True:
            rows = self.dbm.view.media_attachment(group=True, reduce=True, key=form_model_id)
            count = rows[0][u"value"] + 1 if rows else 1
            yield count

    def _create_document(self, old_name, new_name):
        media_file = self.media[old_name]
        size_in_mb = float(media_file.size) / ONE_MB
        media = Media(self.dbm, new_name, size_in_mb, self.form_model.id)
        media.save()
        return media_file

    def _get_media_fields_and_update_values(self, fields, values, counter):
        media_files = {}
        media_field_types = [field_attributes.PHOTO, field_attributes.VIDEO, field_attributes.AUDIO]
        for field in fields:
            if field.is_field_set:
                for value in values:
                    media_files.update(
                        self._get_media_fields_and_update_values(field.fields, value[field.code], counter))
            elif field.type in media_field_types:
                for value in values:
                    old_name = value[field.code]
                    if old_name:
                        count = next(counter)
                        new_name = str(count) + '-' + old_name
                        value[field.code] = new_name
                        media_files[new_name] = self._create_document(old_name, new_name)
        return media_files