import inspect
import os
from tempfile import NamedTemporaryFile

from PIL import Image
from mangrove.form_model.form_model import NAME_FIELD
from mangrove.transport.player.parser import WebParser, SMSParserFactory, XFormParser
from mangrove.transport.repository.survey_responses import get_survey_response_document
from mangrove.transport.services.MediaSubmissionService import MediaSubmissionService
from mangrove.transport.services.survey_response_service import SurveyResponseService
from mangrove.transport.repository import reporters
from mangrove.errors.MangroveException import NumberNotRegisteredException


class WebPlayerV2(object):
    def __init__(self, dbm, feeds_dbm=None, admin_id=None):
        self.dbm = dbm
        self.feeds_dbm = feeds_dbm
        self.admin_id = admin_id

    def add_survey_response(self, request, reporter_id, additional_feed_dictionary=None, logger=None):
        assert request is not None
        form_code, values = self._parse(request.message)
        service = SurveyResponseService(self.dbm, logger, self.feeds_dbm, self.admin_id)
        return service.save_survey(form_code, values, [], request.transport,
                                   reporter_id, additional_feed_dictionary)

    def _parse(self, message):
        return WebParser().parse(message)

    def edit_survey_response(self, request, survey_response, owner_id, additional_feed_dictionary=None, logger=None):
        assert request is not None
        form_code, values = self._parse(request.message)
        service = SurveyResponseService(self.dbm, logger, feeds_dbm=self.feeds_dbm, admin_id=self.admin_id)
        return service.edit_survey(form_code, values, [], survey_response,
                                   additional_feed_dictionary, owner_id)

    def delete_survey_response(self, survey_response, additional_details, logger=None):
        assert survey_response is not None
        service = SurveyResponseService(self.dbm, logger, self.feeds_dbm)
        return service.delete_survey(survey_response, additional_details)


class SMSPlayerV2(object):
    def __init__(self, dbm, post_sms_parser_processors, feeds_dbm=None):
        self.post_sms_parser_processor = post_sms_parser_processors if post_sms_parser_processors else []
        self.dbm = dbm
        self.feeds_dbm = feeds_dbm

    def _post_parse_processor(self, form_code, values, extra_elements=None):
        extra_elements = [] if extra_elements is None else extra_elements
        for post_sms_parser_processors in self.post_sms_parser_processor:
            if len(inspect.getargspec(post_sms_parser_processors.process)[0]) == 4:
                response = post_sms_parser_processors.process(form_code, values, extra_elements)
            else:
                response = post_sms_parser_processors.process(form_code, values)
            if response is not None:
                return response

    def add_survey_response(self, request, logger=None, additional_feed_dictionary=None,
                            translation_processor=None):
        form_code, values, extra_elements = self._parse(request.message)
        post_sms_processor_response = self._post_parse_processor(form_code, values, extra_elements)

        if post_sms_processor_response is not None and not post_sms_processor_response.success:
            if logger is not None:
                log_entry = "message:message " + repr(request.message) + "|source: " + request.transport.source + "|"
                log_entry += "Status: False"
                logger.info(log_entry)
            return post_sms_processor_response

        try:
            reporter_entity = reporters.find_reporter_entity(self.dbm, request.transport.source)
            reporter_entity_names = [{NAME_FIELD: reporter_entity.value(NAME_FIELD)}]
            reporter_short_code = reporter_entity.short_code
        except NumberNotRegisteredException:
            reporter_short_code = None
            reporter_entity_names = None

        service = SurveyResponseService(self.dbm, logger, self.feeds_dbm, response=post_sms_processor_response)
        return service.save_survey(form_code, values, reporter_entity_names, request.transport,
                                   reporter_short_code, additional_feed_dictionary=additional_feed_dictionary,
                                   translation_processor=translation_processor)

    def _parse(self, message):
        return SMSParserFactory().getSMSParser(message, self.dbm).parse(message)


class XFormPlayerV2(object):
    def __init__(self, dbm, feeds_dbm=None):
        self.dbm = dbm
        self.feeds_dbm = feeds_dbm

    def _parse(self, message):
        return XFormParser(self.dbm).parse(message)

    def add_survey_response(self, request, reporter_id, logger=None):
        assert request is not None
        form_code, values = self._parse(request.message)
        media_submission_service = MediaSubmissionService(self.dbm, request.media, form_code)
        media_files = media_submission_service.create_media_documents(values)
        service = SurveyResponseService(self.dbm, logger, self.feeds_dbm)
        response = service.save_survey(form_code, values, [], request.transport, reporter_id)
        self._add_new_attachments(media_files, response.survey_response_id)
        thumbnails = self._add_new_attachments(media_files, response.survey_response_id)
        media_submission_service.create_preview_documents(thumbnails)
        return response

    def update_survey_response(self, request, logger=None, survey_response=None, additional_feed_dictionary=None):
        assert request is not None
        form_code, values = self._parse(request.message)
        media_submission_service = MediaSubmissionService(self.dbm, request.media, form_code)
        media_files = media_submission_service.create_media_documents(values)
        service = SurveyResponseService(self.dbm, logger, self.feeds_dbm)
        response = service.edit_survey(form_code, values, [], survey_response, additional_feed_dictionary)
        self._delete_removed_attachments(request, survey_response.id, media_submission_service)
        thumbnails = self._add_new_attachments(media_files, survey_response.id)
        media_submission_service.create_preview_documents(thumbnails)
        return response

    def _add_new_attachments(self, media_files, survey_response_id):
        thumbnails = {}
        if media_files:
            document = get_survey_response_document(self.dbm, survey_response_id)
            for name, file in media_files.iteritems():
                thumb_file = self._get_thumbnail(file)
                if thumb_file:
                    thumb_file.seek(0)
                    thumbnail_name = 'preview_' + name
                    self.dbm.put_attachment(document, thumb_file, attachment_name=thumbnail_name)
                    thumbnails[thumbnail_name] = os.stat(thumb_file.name).st_size
                # Ignore submission xml file from ODK
                if name != 'xml_submission_file':
                    file.seek(0)
                    self.dbm.put_attachment(document, file, attachment_name=name)
        return thumbnails

    def _get_thumbnail(self, file):
        small = 128, 128
        file.seek(0)
        try:
            small_im = Image.open(file)
        except IOError:
            return
        small_im.thumbnail(small, Image.ANTIALIAS)
        small_im.resize(small, Image.ANTIALIAS)
        temp_file = NamedTemporaryFile(suffix='.'+file.name.split('.')[1])
        small_im.save(temp_file, quality=50)
        return temp_file

    def _delete_removed_attachments(self, request, survey_response_id, media_submission_service):
        if request.retain_files and len(request.retain_files) > 0:
            self._keep_attachments(survey_response_id, request.retain_files, media_submission_service)
        else:
            self._delete_all_attachments(survey_response_id, media_submission_service)

    def _keep_attachments(self, survey_response_id, retain_files, media_submission_service):
        survey_response_document = get_survey_response_document(self.dbm, survey_response_id)
        existing_media_attachments = survey_response_document._data.get('_attachments', {})

        for existing_attachment_name in existing_media_attachments.keys():
            if existing_attachment_name not in retain_files:
                media_submission_service.create_media_details_document(
                    existing_media_attachments[existing_attachment_name]['length'] * -1.0, existing_attachment_name)
                self.dbm.delete_attachment(survey_response_document, existing_attachment_name)

    def _delete_all_attachments(self, survey_response_id, media_submission_service):
        survey_response_document = get_survey_response_document(self.dbm, survey_response_id)
        existing_media_attachments = survey_response_document._data.get('_attachments', {})

        for existing_attachment_name in existing_media_attachments.keys():
            media_submission_service.create_media_details_document(
                existing_media_attachments[existing_attachment_name]['length'] * -1.0, existing_attachment_name)
            self.dbm.delete_attachment(survey_response_document, existing_attachment_name)
