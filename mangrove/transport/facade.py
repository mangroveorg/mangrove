# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.form_model.form_model import LOCATION_TYPE_FIELD_NAME, GEO_CODE_FIELD_NAME
from mangrove.form_model.form_model import GLOBAL_REGISTRATION_FORM_ENTITY_TYPE
from mangrove.datastore.queries import get_entity_count_for_type
from mangrove.errors.MangroveException import GeoCodeFormatException, MangroveException
from mangrove.form_model.form_model import ENTITY_TYPE_FIELD_CODE
from mangrove.form_model.location import Location
from mangrove.utils.types import is_empty, is_not_empty

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
    def __init__(self, message, transportInfo, is_update=False):
        assert transportInfo is not None
        assert message is not None
        self.transport = transportInfo
        self.message = message
        self.is_update = is_update

def create_response_from_form_submission(reporters, submission_id, form_submission=None):
    if form_submission is not None:
        return Response(reporters, submission_id, form_submission.saved, form_submission.errors, form_submission.data_record_id,
        form_submission.short_code, form_submission.cleaned_data, form_submission.is_registration, form_submission.entity_type,
        form_submission.form_model.form_code)
    return Response(reporters, submission_id)

class Response(object):
    def __init__(self, reporters, submission_id, survey_response_id, success=False, errors=None, data_record_id=None, short_code=None,
                 cleaned_data=None, is_registration=False, entity_type=None, form_code=None):
        self.reporters = reporters if reporters is not None else []
        self.success = success
        self.submission_id = submission_id
        self.survey_response_id = survey_response_id
        self.errors = errors or {}
        self.datarecord_id = data_record_id
        self.short_code = short_code
        self.processed_data = cleaned_data
        self.is_registration = is_registration
        self.entity_type = entity_type
        self.form_code = form_code

class GeneralWorkFlow(object):
    def process(self, values):
        return values

class ActivityReportWorkFlow(object):
    def __init__(self, form_model, reporter_entity):
        self.form_model = form_model
        self.reporter_entity = reporter_entity

    def process(self, values):
        if is_empty(self.form_model.get_short_code(values)):
            if self.form_model.entity_defaults_to_reporter():
                values[self.form_model.entity_question.code] = self.reporter_entity.short_code
        return values

class RegistrationWorkFlow(object):
    def __init__(self, dbm, form_model, location_tree):
        self.dbm = dbm
        self.form_model = form_model
        self.location_tree = location_tree

    def _generate_short_code_if_empty(self, values):
        if is_empty(self.form_model.get_short_code(values)):
            _set_short_code(self.dbm, self.form_model, values)

    def process(self, values):
        self._generate_short_code_if_empty(values)
        return Location(self.location_tree, self.form_model).process_submission(values)

    def _set_location_data(self, values):
        location_field_code = self._get_location_field_code()
        if location_field_code is None:
            return
        geo_field_code = self._get_geo_field_code()
        display_location, geo_code = values.get(location_field_code), values.get(geo_field_code)
        location_hierarchy = self._get_location_hierarchy_from_location_name(display_location)
        tree = self.location_tree
        if location_hierarchy is [] and is_not_empty(geo_code):
            try:
                lat_string, long_string = tuple(geo_code.split())
                location_hierarchy = tree.get_location_hierarchy_for_geocode(lat=float(lat_string),
                                                                             long=float(long_string))
            except ValueError as e:
                raise GeoCodeFormatException(e.args)
        elif is_not_empty(location_hierarchy) and is_empty(geo_code):
            try:
                translated_geo_code = tree.get_centroid(display_location.split(',')[0], len(location_hierarchy) - 1)
                values[geo_field_code] = "%s %s" % (translated_geo_code[1], translated_geo_code[0])
            except Exception:
                pass
        values[location_field_code] = location_hierarchy

    def _get_location_hierarchy_from_location_name(self, display_location):
        if is_empty(display_location):
            return None
        display_location_list = display_location.lower().split(',')
        if len(display_location_list) > 1:
            display_location_list.reverse()
            return display_location_list
        lowest_level_location = display_location_list[0]
        location_hierarchy = self.get_location_hierarchy(lowest_level_location)
        return location_hierarchy

    def _get_field_code_by_name(self,field_name):
        field = self.form_model.get_field_by_name(name=field_name)
        return field.code if field is not None else None

    def _get_location_field_code(self):
        return self._get_field_code_by_name(LOCATION_TYPE_FIELD_NAME)

    def _get_geo_field_code(self):
        return self._get_field_code_by_name(GEO_CODE_FIELD_NAME)


def _set_short_code(dbm, form_model, values):
    entity_q_code = form_model.entity_question.code
    try:
        if GLOBAL_REGISTRATION_FORM_ENTITY_TYPE in form_model.entity_type:
            values[entity_q_code] = _generate_short_code(dbm, values[ENTITY_TYPE_FIELD_CODE].lower())
        else:
            values[entity_q_code] = _generate_short_code(dbm, form_model.entity_type[0])
    except KeyError:
        raise MangroveException(ENTITY_TYPE_FIELD_CODE + " should be present")



def _generate_short_code(dbm, entity_type):
    current_count = get_entity_count_for_type(dbm, entity_type.lower())
    entity_type_prefix = entity_type[:3] + "%s"
    return  entity_type_prefix % (current_count + 1)