
# coding=utf-8

import inspect

from mangrove.contrib.deletion import ENTITY_DELETION_FORM_CODE
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.errors.MangroveException import MangroveException
from mangrove.form_model.form_model import NAME_FIELD
from mangrove.transport.repository import reporters
from mangrove.transport.player.new_players import SMSPlayerV2
from mangrove.transport.player.parser import WebParser, SMSParserFactory
from mangrove.transport.work_flow import RegistrationWorkFlow
from mangrove.transport.player.handler import handler_factory


class Player(object):
    def __init__(self, dbm, location_tree=None):
        self.dbm = dbm
        self.location_tree = location_tree

    def submit(self, form_model, values, reporter_names, is_update=False):
        try:
            form_model.bind(values)
            cleaned_data, errors = form_model.validate_submission(values=values)
            handler = handler_factory(self.dbm, form_model, is_update)
            response = handler.handle(form_model, cleaned_data, errors,  reporter_names,
                self.location_tree)
            return response
        except MangroveException:
            raise


class SMSPlayer(Player):
    def __init__(self, dbm, location_tree=None, parser=None,
                 post_sms_parser_processors=None, feeds_dbm=None):
        if not post_sms_parser_processors: post_sms_parser_processors = []
        Player.__init__(self, dbm, location_tree)
        self.parser = parser
        self.post_sms_parser_processor = post_sms_parser_processors
        self.feeds_dbm = feeds_dbm

    def _process(self, values, form_code, reporter_entity):
        form_model = get_form_model_by_code(self.dbm, form_code)
        if form_model.is_entity_registration_form():
            values = RegistrationWorkFlow(self.dbm, form_model, self.location_tree).process(values)
        return form_model, values

    def _process_post_parse_callback(self, form_code, values, extra_elements=[]):
        for post_sms_parser_processors in self.post_sms_parser_processor:
            if len(inspect.getargspec(post_sms_parser_processors.process)[0]) == 4:
                response = post_sms_parser_processors.process(form_code, values, extra_elements)
            else:
                response = post_sms_parser_processors.process(form_code, values)
            if response is not None:
                return response

    def _parse(self, message):
        if self.parser is None:
            self.parser = SMSParserFactory().getSMSParser(message, self.dbm)
        return self.parser.parse(message)

    def get_form_model(self, request):
        form_code, values, extra_elements = self._parse(request.message)
        form_model = get_form_model_by_code(self.dbm, form_code)
        return form_model

    def accept(self, request, logger=None, additional_feed_dictionary=None,
               translation_processor=None):
        ''' This is a single point of entry for all SMS based workflows, we do not have  a separation on the view layer for different sms
        workflows, hence we will be branching to different methods here. Current implementation does the parse twice but that will go away
        once the entity registration is separated '''
        form_model = self.get_form_model(request)
        if form_model.is_entity_registration_form() or form_model.form_code == ENTITY_DELETION_FORM_CODE:
            return self.entity_api(request, logger)
        sms_player_v2 = SMSPlayerV2(self.dbm, post_sms_parser_processors=self.post_sms_parser_processor,
            feeds_dbm=self.feeds_dbm)
        return sms_player_v2.add_survey_response(request, logger, additional_feed_dictionary,
                                                 translation_processor=translation_processor)

    def entity_api(self, request, logger):
        form_code, values, extra_elements = self._parse(request.message)
        post_sms_processor_response = self._process_post_parse_callback(form_code, values, extra_elements)

        log_entry = "message:message " + repr(request.message) + "|source: " + request.transport.source + "|"

        if post_sms_processor_response is not None:
            if logger is not None:
                log_entry += "Status: False"
                logger.info(log_entry)
            post_sms_processor_response.is_registration = True
            return post_sms_processor_response

        reporter_entity = reporters.find_reporter_entity(self.dbm, request.transport.source)
        form_model, values = self._process(values, form_code, reporter_entity)
        reporter_entity_names = [{NAME_FIELD: reporter_entity.value(NAME_FIELD)}]
        response = self.submit(form_model, values, reporter_entity_names)
        if logger is not None:
            log_entry += "Status: True" if response.success else "Status: False"
            logger.info(log_entry)
        return response


class WebPlayer(Player):
    def __init__(self, dbm, location_tree=None, parser=None):
        self.parser = parser or WebParser()
        Player.__init__(self, dbm, location_tree)

    def _parse(self, message):
        return self.parser.parse(message)

    def _process(self, form_code, values):
        form_model = get_form_model_by_code(self.dbm, form_code)
        values = RegistrationWorkFlow(self.dbm, form_model, self.location_tree).process(values)
        return form_model, values

    def accept(self, request, logger=None):
        assert request is not None
        form_code, values = self._parse(request.message)
        form_model, values = self._process(form_code, values)
        response = self.submit(form_model, values, [], is_update=request.is_update)

        if logger is not None:
            log_entry = "message: " + str(request.message) + "|source: " + request.transport.source + "|"
            log_entry += "status: True" if response.success else "status: False"
            logger.info(log_entry)

        return response
