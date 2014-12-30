from mangrove.form_model.field import MediaField
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.form_model.media import Media

ONE_MB = 1000000


class MediaSubmissionService():
    def __init__(self, dbm, media, form_code):
        self.dbm = dbm
        self.media = media
        self.form_model = get_form_model_by_code(self.dbm, form_code)

    def create_media_documents(self, values):
        if self.form_model.is_media_type_fields_present and self.media:
            fields = self.form_model.fields
            counter = self._get_count()
            return self._get_media_fields_and_update_values(fields, [values], counter)
        else:
            return None

    def _get_count(self):
        while True:
            rows = self.dbm.view.media_attachment(group=True, reduce=True, key=self.form_model.id)
            count = rows[0][u"value"] + 1 if rows else 1
            yield count

    def create_media_details_document(self, file_size, name):
        size_in_mb = file_size / ONE_MB
        media = Media(self.dbm, name, size_in_mb, self.form_model.id)
        media.save()

    def _get_media_fields_and_update_values(self, fields, values, counter):
        media_files = {}
        for field in fields:
            if field.is_field_set:
                for value in values:
                    media_files.update(
                        self._get_media_fields_and_update_values(field.fields, value[field.code], counter))
            elif isinstance(field, MediaField):
                for value in values:
                    old_name = value[field.code]
                    if old_name:
                        count = next(counter)
                        new_name = str(count) + '-' + old_name
                        value[field.code] = new_name
                        media_file = self.media[old_name]
                        self.create_media_details_document(float(media_file.size), new_name)
                        media_files[new_name] = media_file
        return media_files