import base64
import inspect
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
        media_submission_service = MediaSubmissionService(self.dbm, logger, request.media, form_code)
        attachments = media_submission_service.create_media_documents(values)
        service = SurveyResponseService(self.dbm, logger, self.feeds_dbm)
        response = service.save_survey(form_code, values, [], request.transport, reporter_id)
        if attachments:
            self.add_new_attachments(attachments, response.survey_response_id)
        return response

    def update_survey_response(self, request, logger=None, survey_response=None, additional_feed_dictionary=None):
        assert request is not None
        form_code, values = self._parse(request.message)
        service = SurveyResponseService(self.dbm, logger, self.feeds_dbm)
        response = service.edit_survey(form_code, values, [], survey_response, additional_feed_dictionary)
        self.delete_removed_attachments(request, survey_response.id)
        self.add_new_attachments(request.media, survey_response.id)

        return response

    def add_new_attachments(self, media_files, survey_response_id):
        for name, file in media_files.iteritems():
            # TODO may be we don't need this check
            if name != 'xml_submission_file':
                self.dbm.put_attachment(get_survey_response_document(self.dbm, survey_response_id),
                                        file, attachment_name=name)

    def delete_removed_attachments(self, request, survey_response_id):
        survey_responce_doc = get_survey_response_document(self.dbm, survey_response_id)
        #TODO can get_attachment method be added to survey_doc
        existing_media = survey_responce_doc._data.get('_attachments', {}).keys()

        if request.retain_files and len(request.retain_files) > 0:
            self.keep_attachments(survey_response_id, existing_media, request.retain_files)
        else:
            self.delete_all_attachments(survey_response_id, existing_media)


    def keep_attachments(self, survey_response_id, existing_attachments, retain_files):
        for existing_attachment in existing_attachments:
            if existing_attachment not in retain_files:
                self.dbm.delete_attachment(get_survey_response_document(self.dbm, survey_response_id),
                                           existing_attachment)

    def delete_all_attachments(self, survey_response_id, existing_attachments):
        for existing_attachment in existing_attachments:
            self.dbm.delete_attachment(get_survey_response_document(self.dbm, survey_response_id),
                                       existing_attachment)