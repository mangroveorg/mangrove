# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import time
from datawinners.location.LocationTree import get_location_tree
from mangrove.datastore import entity
from mangrove.errors.MangroveException import MangroveException, GeoCodeFormatException, InactiveFormModelException
from mangrove.form_model.form_model import get_form_model_by_code, ENTITY_TYPE_FIELD_CODE, NAME_FIELD, LOCATION_TYPE_FIELD_CODE, GEO_CODE
from mangrove.transport import reporter
from mangrove.transport.player.parser import SMSParser, WebParser
from mangrove.transport.submissions import  SubmissionRequest, SubmissionHandler, SubmissionLogger, SubmissionResponse, ENTITY_QUESTION_DISPLAY_CODE
from mangrove.utils.types import is_empty



class Channel(object):
    SMS = "sms"
    WEB = "web"
    XFORMS = "xforms"
    CSV = "csv"
    XLS = "xls"


class TransportInfo(object):
    def __init__(self, transport, source, destination):
        assert transport is not None
        assert source is not None
        assert destination is not None
        self.transport = transport
        self.source = source
        self.destination = destination


class Request(object):
    def __init__(self, message, transportInfo):
        assert transportInfo is not None
        assert message is not None
        self.transport = transportInfo
        self.message = message


class Response(object):
    def __init__(self, reporters, submission_response):
        self.reporters = reporters if reporters is not None else []
        self.success = False
        self.errors = {}
        if submission_response is not None:
            self.success = submission_response.success
            self.submission_id = submission_response.submission_id
            self.errors = submission_response.errors
            self.datarecord_id = submission_response.datarecord_id
            self.short_code = submission_response.short_code
            self.processed_data = submission_response.processed_data
            self.is_registration = submission_response.is_registration
            self.bound_form = submission_response.bound_form


def _short_code_not_in(entity_q_code, values):
    return is_empty(values.get(entity_q_code))


def _epoch_last_three_digit():
    epoch = long(time.time() * 100)
    epoch_last_three_digit = divmod(epoch, 1000)[1]
    return epoch_last_three_digit


def _generate_short_code(dbm, entity_type):
    current_count = entity.get_entity_count_for_type(dbm, entity_type)
    entity_type_prefix = entity_type[:3] + "%s"
    return  entity_type_prefix % (current_count + 1)


def _generate_short_code_if_registration_form(dbm, form_model, values):
    entity_q_code = form_model.entity_question.code
    if _short_code_not_in(entity_q_code, values):
        values[entity_q_code] = _generate_short_code(dbm, values[ENTITY_TYPE_FIELD_CODE].lower())


class Player(object):

    def __init__(self, dbm, submission_handler=None, location_tree=None):
        self.dbm = dbm
        self.submission_handler = SubmissionHandler(dbm) if submission_handler is None else submission_handler
        self.location_tree = get_location_tree() if location_tree is None else location_tree
        self.logger = SubmissionLogger(self.dbm)

    def submit(self, dbm, submission_handler, transportInfo, form_code, values, reporter_entity=None):
        self._handle_registration_form(dbm, form_code, values)
        submission_request = SubmissionRequest(form_code=form_code, submission=values, transport=transportInfo.transport,
                                               source=transportInfo.source, destination=transportInfo.destination,
                                               reporter=reporter_entity)
        submission_id = self.logger.create_submission_log(submission_request)
        try:
            submission_response = self._accept(submission_request,submission_id)
            self.logger.update_submission_log(submission_id=submission_id, data_record_id=submission_response.datarecord_id,
                                              status=submission_response.success, errors=submission_response.errors, in_test_mode=self.form.is_in_test_mode())

            submission_response.submission_id = submission_id
            return submission_response
        except MangroveException as e:
            self.logger.update_submission_log(submission_id=submission_id,status=False,errors = e.message, in_test_mode=self.form.is_in_test_mode())
            raise


    def _accept(self, request,submission_id):
        assert isinstance(request, SubmissionRequest)
        form_code = request.form_code
        values = request.submission

        self.form = get_form_model_by_code(self.dbm, form_code)
        self.form.bind(values)
        if self.form.entity_defaults_to_reporter():
            self._set_entity_short_code(request.reporter.short_code, values)

        form_submission = self._submit(self.form, values, submission_id)

        return SubmissionResponse(form_submission.saved, submission_id, form_submission.errors, form_submission.data_record_id, short_code=form_submission.short_code,
                                  processed_data=form_submission.cleaned_data,is_registration = self.form.is_registration_form(), bound_form=self.form)


    def _submit(self, form, values, submission_id):
        self._reject_submission_for_inactive_forms(form)

        form_submission = form.validate_submission(values)

        if form_submission.is_valid:
            form_submission.save(self.dbm, submission_id)

        return form_submission

    def _should_accept_submission(self, form):
        return form.is_inactive()

    def _reject_submission_for_inactive_forms(self, form):
        if self._should_accept_submission(form):
            raise InactiveFormModelException(form.form_code)

    def _set_entity_short_code(self, short_code, values):
        values[ENTITY_QUESTION_DISPLAY_CODE] = short_code


    def _get_location_heirarchy_from_location_name(self, display_location):
        if is_empty(display_location):
            return None
        display_location_list = display_location.lower().split(',')
        if len(display_location_list) > 1:
            display_location_list.reverse()
            return display_location_list
        lowest_level_location = display_location_list[0]
        tree = self.location_tree
        location_hierarchy = tree.get_hierarchy_path(lowest_level_location)
        return location_hierarchy


    def _get_location_data(self, values):
        display_location, geo_code = values.get(LOCATION_TYPE_FIELD_CODE), values.get(GEO_CODE)
        location_hierarchy = self._get_location_heirarchy_from_location_name(display_location)
        tree = self.location_tree
        if location_hierarchy is None and not is_empty(geo_code):
            try:
                lat_string, long_string = tuple(geo_code.split())
                location_hierarchy = tree.get_location_hierarchy_for_geocode(lat=float(lat_string), long=float(long_string))
            except ValueError as e:
                raise GeoCodeFormatException(e.args)
        elif location_hierarchy is not None and is_empty(geo_code):
            try:
                translated_geo_code = tree.get_centroid(display_location.split(',')[0],len(location_hierarchy)-1)
                values[GEO_CODE] = "%s %s" % (translated_geo_code[1], translated_geo_code[0])
            except Exception:
                pass
        values[LOCATION_TYPE_FIELD_CODE] = location_hierarchy

    def _handle_registration_form(self, dbm, form_code, values):
        form_model = get_form_model_by_code(dbm, form_code)
        if form_model.is_registration_form():
            _generate_short_code_if_registration_form(dbm, form_model, values)
            self._get_location_data(values)


class SMSPlayer(Player):
    def __init__(self, dbm, submission_handler, location_tree=None):
        Player.__init__(self, dbm, submission_handler, location_tree)

    def _parse(self, request):
        sms_parser = SMSParser()
        form_code, values = sms_parser.parse(request.message)
        return form_code, values

    def accept(self, request):
        assert request is not None
        reporter_entity,reporter_name = reporter.find_reporter_entity(self.dbm, request.transport.source)
        form_code, values = self._parse(request)
        submission_response = self.submit(self.dbm, self.submission_handler, request.transport, form_code, values, reporter_entity)
        return Response(reporters=[{ NAME_FIELD : reporter_name}], submission_response=submission_response)


class WebPlayer(Player):
    def __init__(self, dbm, submission_handler=None, location_tree=None):
        Player.__init__(self, dbm, submission_handler, location_tree)


    def _parse(self, request):
        web_parser = WebParser()
        form_code, values = web_parser.parse(request.message)
        return form_code, values

    def accept(self, request):
        assert request is not None
        form_code, values = self._parse(request)
        submission_response = self.submit(self.dbm, self.submission_handler, request.transport, form_code, values)
        return Response(reporters=[], submission_response=submission_response)


class CsvPlayer(Player):
    def __init__(self, dbm, submission_handler, parser, location_tree=None):
        Player.__init__(self, dbm, submission_handler, location_tree)
        self.parser = parser

    def accept(self, csv_data):
        responses = []
        submissions = self.parser.parse(csv_data)
        for (form_code, values) in submissions:
            try:
                transport_info = TransportInfo(transport=Channel.CSV, source=Channel.CSV, destination="")
                submission_response = self.submit(self.dbm, self.submission_handler, transport_info, form_code, values)
                response = Response(reporters=[], submission_response=submission_response)
                if not submission_response.success:
                    response.errors = dict(error=submission_response.errors.values(), row=values)
                responses.append(response)
            except MangroveException as e:
                response = Response(reporters=[], submission_response=None)
                response.success = False
                response.errors = dict(error=e.message, row=values)
                responses.append(response)
        return responses


class XlsPlayer(Player):
    def __init__(self, dbm, submission_handler, parser, location_tree=None):
        Player.__init__(self, dbm, submission_handler, location_tree)
        self.parser = parser

    def accept(self, file_contents):
        responses = []
        submissions = self.parser.parse(file_contents)
        for (form_code, values) in submissions:
            try:
                transport_info = TransportInfo(transport=Channel.XLS, source=Channel.XLS, destination="")
                submission_response = self.submit(self.dbm, self.submission_handler, transport_info, form_code, values)
                response = Response(reporters=[], submission_response=submission_response)
                if not submission_response.success:
                    response.errors = dict(error=submission_response.errors.values(), row=values)
                responses.append(response)
            except MangroveException as e:
                response = Response(reporters=[], submission_response=None)
                response.success = False
                response.errors = dict(error=e.message, row=values)
                responses.append(response)
        return responses



        