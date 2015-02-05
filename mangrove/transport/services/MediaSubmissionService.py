import logging
from mangrove.form_model.field import MediaField
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.form_model.media import Media

ONE_MB = 1000000

logger = logging.getLogger('media-submission')

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

    def create_media_details_document(self, file_size, name, is_preview=False):
        size_in_mb = file_size / ONE_MB
        media = Media(self.dbm, name, size_in_mb, self.form_model.id, is_preview)
        media.save()

    def create_preview_documents(self, thumbnails):
        for name, size in thumbnails.iteritems():
            self.create_media_details_document(float(size), name, is_preview=True)

    def _get_media_fields_and_update_values(self, fields, values, counter):
        media_files = {}
        for field in fields:
            if field.is_field_set:
                for value in values:
                    media_files.update(
                        self._get_media_fields_and_update_values(field.fields, value[field.code], counter))
            elif isinstance(field, MediaField):
                for value in values:
                    old_name = value.get(field.code)
                    if old_name:
                        media_file = self.media.get(old_name)
                        if media_file:
                            count = next(counter)
                            new_name = str(count) + '-' + old_name
                            value[field.code] = new_name
                            self.create_media_details_document(float(media_file.size), new_name)
                            media_files[new_name] = media_file
                        else:
                            logger.error("'%s' not found in [%s]" % (old_name, ",".join(self.media.keys())))
        return media_files