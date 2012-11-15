# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from copy import copy
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.errors.MangroveException import MangroveException, InactiveFormModelException
from mangrove.form_model.form_model import NAME_FIELD
from mangrove.transport import reporter
from mangrove.transport.player.parser import WebParser, SMSParserFactory, XFormParser
from mangrove.transport.submissions import  Submission
from mangrove.transport.facade import  ActivityReportWorkFlow, RegistrationWorkFlow, GeneralWorkFlow
from mangrove.transport.player.handler import handler_factory
from mangrove.utils.types import is_empty
import inspect


class Player(object):
    def __init__(self, dbm, location_tree=None):
        self.dbm = dbm
        self.location_tree = location_tree

    def _create_submission(self, transport_info, form_code, values):
        form_model = get_form_model_by_code(self.dbm, form_code)
        submission = Submission(self.dbm, transport_info, form_code, form_model.revision, values)
        submission.save()
        return submission


    def submit(self, form_model, values, submission, reporter_names, is_update=False):
        try:
            if form_model.is_inactive():
                raise InactiveFormModelException(form_model.form_code)
            form_model.bind(values)
            cleaned_data, errors = form_model.validate_submission(values=values)
            handler = handler_factory(self.dbm, form_model, is_update)
            response = handler.handle(form_model, cleaned_data, errors, submission.uuid, reporter_names, self.location_tree)
            submission.values[form_model.entity_question.code] = response.short_code
            submission.update(response.success, response.errors, response.datarecord_id,
                form_model.is_in_test_mode())
            return response
        except MangroveException as exception:
            submission.update(status=False, errors=exception.message, is_test_mode=form_model.is_in_test_mode())
            raise


class SMSPlayer(Player):
    def __init__(self, dbm, location_tree=None, parser=None,
                 post_sms_parser_processors=None):
        if not post_sms_parser_processors: post_sms_parser_processors = []
        Player.__init__(self, dbm, location_tree)
        self.parser = parser
        self.post_sms_parser_processor = post_sms_parser_processors

    def _process(self, values, form_code, reporter_entity):
        form_model = get_form_model_by_code(self.dbm, form_code)
        values = GeneralWorkFlow().process(values)
        if form_model.is_registration_form():
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

    def accept(self, request):
        form_code, values, extra_elements = self._parse(request.message)
        post_sms_processor_response = self._process_post_parse_callback(form_code, values, extra_elements)
        if post_sms_processor_response is not None:
            return post_sms_processor_response

        reporter_entity = reporter.find_reporter_entity(self.dbm, request.transport.source)
        submission = self._create_submission(request.transport, form_code, copy(values))
        form_model, values = self._process(values, form_code, reporter_entity)
        reporter_entity_names = [{NAME_FIELD: reporter_entity.value(NAME_FIELD)}]
        return self.submit(form_model, values, submission, reporter_entity_names)


class WebPlayer(Player):
    def __init__(self, dbm, location_tree=None, parser=None):
        self.parser = parser or WebParser()
        Player.__init__(self, dbm, location_tree)

    def _parse(self, message):
        return self.parser.parse(message)

    def _process(self, form_code, values):
        form_model = get_form_model_by_code(self.dbm, form_code)
        values = GeneralWorkFlow().process(values)
        if form_model.is_registration_form():
            values = RegistrationWorkFlow(self.dbm, form_model, self.location_tree).process(values)

        return form_model, values

    def accept(self, request):
        assert request is not None
        form_code, values = self._parse(request.message)
        submission = self._create_submission(request.transport, form_code, copy(values))
        form_model, values = self._process(form_code, values)
        return self.submit(form_model, values, submission, [], is_update=request.is_update)


class XFormPlayer(Player):
    def __init__(self, dbm):
        self.parser = XFormParser(dbm)
        Player.__init__(self, dbm)

    def _parse(self, message):
        return self.parser.parse(message)

    def accept(self, request):
        assert request is not None
        form_code, values = self._parse(request.message)

        submission = self._create_submission(request.transport, form_code, copy(values))
        form_model = get_form_model_by_code(self.dbm, form_code)

        return self.submit(form_model, values, submission, [])
