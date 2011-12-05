# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from copy import copy
import time
from datawinners import settings
from datawinners.location.LocationTree import get_location_hierarchy
from mangrove.datastore.queries import get_entity_count_for_type
from mangrove.errors.MangroveException import MangroveException, GeoCodeFormatException
from mangrove.form_model.form_model import get_form_model_by_code, ENTITY_TYPE_FIELD_CODE, NAME_FIELD, LOCATION_TYPE_FIELD_CODE, GEO_CODE
from mangrove.transport import reporter
from mangrove.transport.player.parser import KeyBasedSMSParser, WebParser
from mangrove.transport.submissions import  Submission
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
    def __init__(self, reporters, submission_id, form_submission):
        self.reporters = reporters if reporters is not None else []
        self.success = False
        self.errors = {}
        if form_submission is not None:
            self.success = form_submission.saved
            self.submission_id = submission_id
            self.errors = form_submission.errors
            self.datarecord_id = form_submission.data_record_id
            self.short_code = form_submission.short_code
            self.processed_data = form_submission.cleaned_data
            self.is_registration = form_submission.is_registration
            self.entity_type = form_submission.entity_type


def _short_code_not_in(entity_q_code, values):
    return is_empty(values.get(entity_q_code))


def _epoch_last_three_digit():
    epoch = long(time.time() * 100)
    epoch_last_three_digit = divmod(epoch, 1000)[1]
    return epoch_last_three_digit


def _generate_short_code(dbm, entity_type):
    current_count = get_entity_count_for_type(dbm, entity_type)
    entity_type_prefix = entity_type[:3] + "%s"
    return  entity_type_prefix % (current_count + 1)


def _set_short_code(dbm, form_model, values):
    entity_q_code = form_model.entity_question.code
    try:
        values[entity_q_code] = _generate_short_code(dbm, values[ENTITY_TYPE_FIELD_CODE].lower())
    except KeyError:
        raise MangroveException(ENTITY_TYPE_FIELD_CODE + " should be present")

class Player(object):
    def __init__(self, dbm, location_tree=None):
        self.dbm = dbm
        self.location_tree = location_tree

    def submit(self, transportInfo, form_code, values, reporter_entity=None):
        submission = Submission(self.dbm, transportInfo, form_code, copy(values))
        submission.save()
        try:
            form_submission = self._save_submission(form_code, values, reporter_entity, submission.uuid)
            submission.update(form_submission.saved, form_submission.errors, form_submission.data_record_id,
                              form_submission.form_model.is_in_test_mode())
            return submission.uuid, form_submission
        except MangroveException as exception:
            submission.update(status=False, errors=exception.message, is_test_mode=self.form.is_in_test_mode())
            raise

    def _update_submission_with_short_code_if_activity_report(self, reporter_entity, values):
        if self.form.entity_defaults_to_reporter():
            self._set_entity_short_code(reporter_entity.short_code, values)

    def _update_submission_with_short_code_if_not_submitted(self, reporter_entity, form, values):
        if self._short_code_submitted(form, values):
            return
        self._update_submission_with_short_code_if_activity_report(reporter_entity, values)
        self._update_submission_with_short_code_if_registration_form(self.dbm, form, values)

    def _update_submission_if_required(self, reporter_entity, values):
        self._update_submission_with_short_code_if_not_submitted(reporter_entity, self.form, values)
        self._update_submission_with_location_if_registration_form(self.form, values)

    def _save_submission(self, form_code, values, reporter_entity, submission_id):
        self.form = get_form_model_by_code(self.dbm, form_code)
        self._update_submission_if_required(reporter_entity, values)
        form_submission = self.form.submit(self.dbm, values, submission_id)
        return form_submission

    def _set_entity_short_code(self, short_code, values):
        values[self.form.entity_question.code] = short_code

    def _get_location_hierarchy_from_location_name(self, display_location):
        if is_empty(display_location):
            return None
        display_location_list = display_location.lower().split(',')
        if len(display_location_list) > 1:
            display_location_list.reverse()
            return display_location_list
        lowest_level_location = display_location_list[0]
        location_hierarchy = get_location_hierarchy(lowest_level_location)
        return location_hierarchy


    def _set_location_data(self, values):
        display_location, geo_code = values.get(LOCATION_TYPE_FIELD_CODE), values.get(GEO_CODE)
        location_hierarchy = self._get_location_hierarchy_from_location_name(display_location)
        tree = self.location_tree
        if location_hierarchy is [] and not is_empty(geo_code):
            try:
                lat_string, long_string = tuple(geo_code.split())
                location_hierarchy = tree.get_location_hierarchy_for_geocode(lat=float(lat_string),
                                                                             long=float(long_string))
            except ValueError as e:
                raise GeoCodeFormatException(e.args)
        elif location_hierarchy is not [] and is_empty(geo_code):
            try:
                translated_geo_code = tree.get_centroid(display_location.split(',')[0], len(location_hierarchy) - 1)
                values[GEO_CODE] = "%s %s" % (translated_geo_code[1], translated_geo_code[0])
            except Exception:
                pass
        values[LOCATION_TYPE_FIELD_CODE] = location_hierarchy

    def _update_submission_with_short_code_if_registration_form(self, dbm, form_model, values):
        if form_model.is_registration_form():
            _set_short_code(dbm, form_model, values)

    def _update_submission_with_location_if_registration_form(self, form_model, values):
        if form_model.is_registration_form():
            self._set_location_data(values)

    def _short_code_submitted(self, form, values):
        return not is_empty(form.get_short_code(values))


class SMSPlayer(Player):
    def __init__(self, dbm, location_tree=None, parser=None):
        Player.__init__(self, dbm, location_tree)
        self.parser = parser or KeyBasedSMSParser()

    def accept(self, transport_info, form_code, values):
        reporter_entity = reporter.find_reporter_entity(self.dbm, transport_info.source)
        submission_id, form_submission = self.submit(transport_info, form_code, values, reporter_entity)
        return Response(reporters=[{NAME_FIELD: reporter_entity.value(NAME_FIELD)}], submission_id=submission_id,
                        form_submission=form_submission)

class WebPlayer(Player):
    def __init__(self, dbm, location_tree=None):
        Player.__init__(self, dbm, location_tree)


    def _parse(self, request):
        web_parser = WebParser()
        form_code, values = web_parser.parse(request.message)
        return form_code, values

    def accept(self, request):
        assert request is not None
        form_code, values = self._parse(request)
        submission_id, form_submission = self.submit(request.transport, form_code, values)
        return Response(reporters=[], submission_id=submission_id, form_submission=form_submission)

class FilePlayer(Player):
    def __init__(self, dbm, parser, channel_name, location_tree=None):
        Player.__init__(self, dbm, location_tree)
        self.parser = parser
        self.channel_name = channel_name

    def accept(self, file_contents):
        responses = []
        submissions = self.parser.parse(file_contents)
        for (form_code, values) in submissions:
            try:
                transport_info = TransportInfo(transport=self.channel_name, source=self.channel_name, destination="")
                submission_id, form_submission = self.submit(transport_info, form_code, values)
                response = Response(reporters=[], submission_id=submission_id, form_submission=form_submission)
                if not form_submission.saved:
                    response.errors = dict(error=form_submission.errors, row=values)
                responses.append(response)
            except MangroveException as e:
                response = Response(reporters=[], submission_id=None, form_submission=None)
                response.success = False
                response.errors = dict(error=e.message, row=values)
                responses.append(response)
        return responses



        