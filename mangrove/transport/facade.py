# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.form_model.form_model import LOCATION_TYPE_FIELD_NAME, GEO_CODE_FIELD_NAME
from mangrove.form_model.form_model import GLOBAL_REGISTRATION_FORM_ENTITY_TYPE
from mangrove.datastore.queries import get_entity_count_for_type
from mangrove.errors.MangroveException import GeoCodeFormatException, MangroveException
from mangrove.form_model.form_model import ENTITY_TYPE_FIELD_CODE, LOCATION_TYPE_FIELD_CODE, GEO_CODE
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
    def __init__(self, reporters, submission_id, form_submission=None):
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
    def __init__(self, dbm, form_model, location_tree, get_location_hierarchy):
        self.dbm = dbm
        self.form_model = form_model
        self.location_tree = location_tree
        self.get_location_hierarchy = get_location_hierarchy

    def _generate_short_code_if_empty(self, values):
        if is_empty(self.form_model.get_short_code(values)):
            _set_short_code(self.dbm, self.form_model, values)

    def process(self, values):
        self._generate_short_code_if_empty(values)
        self._set_location_data(values)
        return values

    def _set_location_data(self, values):
        location_field_code = self._get_location_field_code()
        geo_field_code = self._get_geo_field_code()
        display_location, geo_code = values.get(location_field_code), values.get(geo_field_code)
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