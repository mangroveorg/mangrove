import inspect
from mangrove.form_model.form_model import NAME_FIELD, get_form_model_by_code
from mangrove.transport.player.parser import WebParser, SMSParserFactory, XFormParser
from mangrove.transport.services.survey_response_service import SurveyResponseService
from mangrove.utils.types import is_empty
from mangrove.transport.repository import reporters

class WebPlayerV2(object):
    def __init__(self, dbm, feeds_dbm=None):
        self.dbm = dbm
        self.feeds_dbm = feeds_dbm

    def add_survey_response(self, request, logger=None):
        assert request is not None
        form_code, values = self._parse(request.message)
        service = SurveyResponseService(self.dbm, logger, self.feeds_dbm)
        return service.save_survey(form_code, values, [], request.transport, request.message)

    def _parse(self, message):
        return WebParser().parse(message)

    def edit_survey_response(self, request, survey_response, logger=None):
        assert request is not None
        form_code, values = self._parse(request.message)
        service = SurveyResponseService(self.dbm, logger)
        return service.edit_survey(form_code, values, [], request.transport, request.message, survey_response)

    def delete_survey_response(self, survey_response, logger=None):
        assert survey_response is not None
        service = SurveyResponseService(self.dbm, logger)
        return service.delete_survey([], survey_response)


class SMSPlayerV2(object):
    def __init__(self, dbm, post_sms_parser_processors, feeds_dbm=None):
        self.post_sms_parser_processor = post_sms_parser_processors if post_sms_parser_processors else []
        self.dbm = dbm
        self.feeds_dbm = feeds_dbm

    def _post_parse_processor(self, form_code, values, extra_elements=[]):
        for post_sms_parser_processors in self.post_sms_parser_processor:
            if len(inspect.getargspec(post_sms_parser_processors.process)[0]) == 4:
                response = post_sms_parser_processors.process(form_code, values, extra_elements)
            else:
                response = post_sms_parser_processors.process(form_code, values)
            if response is not None:
                return response

    def add_survey_response(self, request, logger=None, additional_feed_dictionary=None):
        form_code, values, extra_elements = self._parse(request.message)
        post_sms_processor_response = self._post_parse_processor(form_code, values, extra_elements)

        if post_sms_processor_response is not None:
            if logger is not None:
                log_entry = "message:message " + repr(request.message) + "|source: " + request.transport.source + "|"
                log_entry += "Status: False"
                logger.info(log_entry)
            return post_sms_processor_response

        reporter_entity = reporters.find_reporter_entity(self.dbm, request.transport.source)
        reporter_entity_names = [{NAME_FIELD: reporter_entity.value(NAME_FIELD)}]

        values = self._use_reporter_as_entity_if_summary_report(form_code, values, reporter_entity.short_code)
        service = SurveyResponseService(self.dbm, logger, self.feeds_dbm)
        return service.save_survey(form_code, values, reporter_entity_names, request.transport, request.message,
            additional_feed_dictionary)

    def _use_reporter_as_entity_if_summary_report(self, form_code, values, reporter_entity_short_code):
        form_model = get_form_model_by_code(self.dbm, form_code)
        if form_model.entity_defaults_to_reporter() and  is_empty(form_model.get_short_code(values)):
            values[form_model.entity_question.code] = reporter_entity_short_code
        return values

    def _parse(self, message):
        return SMSParserFactory().getSMSParser(message, self.dbm).parse(message)


class XFormPlayerV2(object):
    def __init__(self, dbm, feeds_dbm=None):
        self.dbm = dbm
        self.feeds_dbm = feeds_dbm

    def _parse(self, message):
        return XFormParser(self.dbm).parse(message)

    def add_survey_response(self, request, logger=None):
        assert request is not None
        form_code, values = self._parse(request.message)
        service = SurveyResponseService(self.dbm, logger, self.feeds_dbm)
        return service.save_survey(form_code, values, [], request.transport, request.message)

