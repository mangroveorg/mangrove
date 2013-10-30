# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# coding=utf-8

from copy import copy
from mangrove.contrib.deletion import ENTITY_DELETION_FORM_CODE
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.errors.MangroveException import MangroveException, InactiveFormModelException, FormModelDoesNotExistsException
from mangrove.form_model.form_model import NAME_FIELD
from mangrove.transport.repository import reporters
from mangrove.transport.player.new_players import SMSPlayerV2
from mangrove.transport.player.parser import WebParser, SMSParserFactory
from mangrove.transport.contract.submission import Submission
from mangrove.transport.work_flow import ActivityReportWorkFlow, RegistrationWorkFlow, GeneralWorkFlow
from mangrove.transport.player.handler import handler_factory
import inspect


class Player(object):
    def __init__(self, dbm, location_tree=None):
        self.dbm = dbm
        self.location_tree = location_tree

    def _create_submission(self, transport_info, form_code, values):
        try:
            form_model = get_form_model_by_code(self.dbm, form_code)
            form_model_revision = form_model.revision
        except FormModelDoesNotExistsException:
            form_model_revision = None

        submission = Submission(self.dbm, transport_info, form_code, form_model_revision, values)
        submission.save()
        return submission


    def submit(self, form_model, values, submission, reporter_names, is_update=False):
        try:
            if form_model.is_inactive():
                raise InactiveFormModelException(form_model.form_code)
            form_model.bind(values)
            cleaned_data, errors = form_model.validate_submission(values=values)
            handler = handler_factory(self.dbm, form_model, is_update)
            response = handler.handle(form_model, cleaned_data, errors, submission.uuid, reporter_names,
                self.location_tree)
            submission.update(response.success, response.errors, form_model.entity_question.code, response.short_code,
                response.datarecord_id, form_model.is_in_test_mode())
            return response
        except MangroveException as exception:
            submission.update(status=False, errors=exception.message, is_test_mode=form_model.is_in_test_mode())
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
        values = GeneralWorkFlow().process(values)
        if form_model.is_entity_registration_form():
            values = RegistrationWorkFlow(self.dbm, form_model, self.location_tree).process(values)
        if form_model.entity_defaults_to_reporter():
            values = ActivityReportWorkFlow(form_model, reporter_entity).process(values)

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

    def accept(self, request, logger=None, additional_feed_dictionary=None):
        ''' This is a single point of entry for all SMS based workflows, we do not have  a separation on the view layer for different sms
        workflows, hence we will be branching to different methods here. Current implementation does the parse twice but that will go away
        once the entity registration is separated '''
        form_code, values, extra_elements = self._parse(request.message)
        form_model = get_form_model_by_code(self.dbm, form_code)
        if form_model.is_entity_registration_form() or form_model.form_code == ENTITY_DELETION_FORM_CODE:
            return self.entity_api(request, logger)
        sms_player_v2 = SMSPlayerV2(self.dbm, post_sms_parser_processors=self.post_sms_parser_processor,
            feeds_dbm=self.feeds_dbm)
        return sms_player_v2.add_survey_response(request, logger, additional_feed_dictionary)

    def entity_api(self, request, logger):
        form_code, values, extra_elements = self._parse(request.message)
        post_sms_processor_response = self._process_post_parse_callback(form_code, values, extra_elements)

        log_entry = "message:message " + repr(request.message) + "|source: " + request.transport.source + "|"

        if post_sms_processor_response is not None:
            if logger is not None:
                log_entry += "Status: False"
                logger.info(log_entry)
            return post_sms_processor_response

        reporter_entity = reporters.find_reporter_entity(self.dbm, request.transport.source)
        submission = self._create_submission(request.transport, form_code, copy(values))
        form_model, values = self._process(values, form_code, reporter_entity)
        reporter_entity_names = [{NAME_FIELD: reporter_entity.value(NAME_FIELD)}]
        response = self.submit(form_model, values, submission, reporter_entity_names)
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
        submission = self._create_submission(request.transport, form_code, copy(values))
        form_model, values = self._process(form_code, values)
        response = self.submit(form_model, values, submission, [], is_update=request.is_update)

        if logger is not None:
            log_entry = "message: " + str(request.message) + "|source: " + request.transport.source + "|"
            log_entry += "status: True" if response.success else "status: False"
            logger.info(log_entry)

        return response
