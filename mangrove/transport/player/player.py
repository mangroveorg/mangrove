# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from copy import copy
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.errors.MangroveException import MangroveException
from mangrove.form_model.form_model import NAME_FIELD
from mangrove.transport import reporter
from mangrove.transport.player.parser import WebParser
from mangrove.transport.submissions import  Submission
from mangrove.transport.facade import Response, ActivityReportWorkFlow, RegistrationWorkFlow, GeneralWorkFlow
from transport.player.parser import SMSParserFactory


class Player(object):
    def __init__(self, dbm, location_tree=None, get_location_hierarchy=None):
        self.dbm = dbm
        self.location_tree = location_tree
        self.get_location_hierarchy = get_location_hierarchy

    def submit(self, transportInfo, form_model, values):
        submission = Submission(self.dbm, transportInfo, form_model.form_code, copy(values))
        submission.save()
        try:
            form_submission = form_model.submit(self.dbm, values, submission.uuid)
            submission.update(form_submission.saved, form_submission.errors, form_submission.data_record_id,
                              form_submission.form_model.is_in_test_mode())
            submission.update_values(form_submission.cleaned_data)
            return submission.uuid, form_submission
        except MangroveException as exception:
            submission.update(status=False, errors=exception.message, is_test_mode=form_model.is_in_test_mode())
            raise

class SMSPlayer(Player):
    def __init__(self, dbm, location_tree=None, parser=None, get_location_hierarchy=None):
        Player.__init__(self, dbm, location_tree, get_location_hierarchy)
        self.parser = parser

    def accept(self, request):
        if self.parser is None:
            self.parser = SMSParserFactory().getSMSParser(request.message, self.dbm)

        reporter_entity = reporter.find_reporter_entity(self.dbm, request.transport.source)
        form_code,values = self.parser.parse(request.message)
        form_model = get_form_model_by_code(self.dbm, form_code)
        values = GeneralWorkFlow().process(values)
        if form_model.is_registration_form():
            values = RegistrationWorkFlow(self.dbm, form_model, self.location_tree, self.get_location_hierarchy).process(values)
        if form_model.entity_defaults_to_reporter():
            values = ActivityReportWorkFlow(form_model, reporter_entity).process(values)
        submission_id, form_submission = self.submit(request.transport, form_model, values)
        return Response(reporters=[{NAME_FIELD: reporter_entity.value(NAME_FIELD)}], submission_id=submission_id,
                        form_submission=form_submission)

class WebPlayer(Player):
    def __init__(self, dbm, location_tree=None, get_location_hierarchy=None):
        Player.__init__(self, dbm, location_tree, get_location_hierarchy)

    def _parse(self, request):
        web_parser = WebParser()
        form_code, values = web_parser.parse(request.message)
        form_model = get_form_model_by_code(self.dbm, form_code)
        values = GeneralWorkFlow().process(values)
        
        if form_model.is_registration_form():
            values = RegistrationWorkFlow(self.dbm, form_model, self.location_tree, self.get_location_hierarchy).process(values)

        return form_model, values

    def accept(self, request):
        assert request is not None
        form_model, values = self._parse(request)
        submission_id, form_submission = self.submit(request.transport, form_model, values)
        return Response(reporters=[], submission_id=submission_id, form_submission=form_submission)



