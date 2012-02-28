# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from copy import copy
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.errors.MangroveException import MangroveException
from mangrove.form_model.form_model import NAME_FIELD
from mangrove.transport import reporter
from mangrove.transport.player.parser import WebParser, SMSParserFactory
from mangrove.transport.submissions import  Submission
from mangrove.transport.facade import Response, ActivityReportWorkFlow, RegistrationWorkFlow, GeneralWorkFlow


class Player(object):
    def __init__(self, dbm, location_tree=None, get_location_hierarchy=None):
        self.dbm = dbm
        self.location_tree = location_tree
        self.get_location_hierarchy = get_location_hierarchy

    def _create_submission(self, transport_info, form_code, values):
        submission = Submission(self.dbm, transport_info, form_code, copy(values))
        submission.save()
        return submission

    def submit(self, form_model, values, submission):
        form_submission = form_model.submit(self.dbm, values)
        submission.update(form_submission.saved, form_submission.errors, form_submission.data_record_id,
            form_submission.form_model.is_in_test_mode())
        return form_submission

class SMSPlayer(Player):
    def __init__(self, dbm, location_tree=None, parser=None, get_location_hierarchy=None,
                 post_sms_parser_processors=None):
        if not post_sms_parser_processors: post_sms_parser_processors = []
        Player.__init__(self, dbm, location_tree, get_location_hierarchy)
        self.parser = parser
        self.post_sms_parser_processor=post_sms_parser_processors

    def _process(self, values, form_code, reporter_entity):
        form_model = get_form_model_by_code(self.dbm, form_code)
        values = GeneralWorkFlow().process(values)
        if form_model.is_registration_form():
            values = RegistrationWorkFlow(self.dbm, form_model, self.location_tree, self.get_location_hierarchy).process(values)
        if form_model.entity_defaults_to_reporter():
            values = ActivityReportWorkFlow(form_model, reporter_entity).process(values)

        return form_model, values

    def _process_post_parse_callback(self, form_code, values):
        for post_sms_parser_processors in self.post_sms_parser_processor:
            response = post_sms_parser_processors.process(form_code, values)
            if response is not None:
                return response

    def _parse(self, request):
        if self.parser is None:
            self.parser = SMSParserFactory().getSMSParser(request.message, self.dbm)
        return self.parser.parse(request.message)

    def accept(self, request):
        form_code, values = self._parse(request)
        post_sms_processor_response = self._process_post_parse_callback(form_code, values)
        if post_sms_processor_response is not None:
            return post_sms_processor_response

        reporter_entity = reporter.find_reporter_entity(self.dbm, request.transport.source)
        submission = self._create_submission(request.transport, form_code, values)
        form_model, values = self._process(values, form_code, reporter_entity)
        try:
            form_submission = self.submit(form_model, values, submission)
        except MangroveException as exception:
            submission.update(status=False, errors=exception.message, is_test_mode=form_model.is_in_test_mode())
            raise
        return Response(reporters=[{NAME_FIELD: reporter_entity.value(NAME_FIELD)}], submission_id=submission.uuid,
                        form_submission=form_submission)

class WebPlayer(Player):
    def __init__(self, dbm, location_tree=None, get_location_hierarchy=None):
        Player.__init__(self, dbm, location_tree, get_location_hierarchy)

    def _parse(self, request):
        web_parser = WebParser()
        form_code, values = web_parser.parse(request.message)
        return form_code, values

    def _process(self, form_code, values):
        form_model = get_form_model_by_code(self.dbm, form_code)
        values = GeneralWorkFlow().process(values)
        if form_model.is_registration_form():
            values = RegistrationWorkFlow(self.dbm, form_model, self.location_tree, self.get_location_hierarchy).process(values)

        return form_model, values

    def accept(self, request):
        assert request is not None
        form_code, values = self._parse(request)
        submission = self._create_submission(request.transport, form_code, values)
        form_model, values = self._process(form_code, values)
        try:
            form_submission = self.submit(form_model, values, submission)
        except MangroveException as exception:
            submission.update(status=False, errors=exception.message, is_test_mode=form_model.is_in_test_mode())
            raise
        return Response(reporters=[], submission_id=submission.uuid, form_submission=form_submission)



