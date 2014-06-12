from mangrove.form_model.field import field_attributes
from mangrove.utils.geo_utils import convert_to_geometry
from mangrove.utils.types import is_empty

LOCATION_TYPE_FIELD_NAME = "location"
LOCATION_TYPE_FIELD_CODE = "l"
GEO_CODE = "g"
GEO_CODE_FIELD_NAME = "geo_code"

class Location(object):
    def __init__(self,location_tree, form_model):
        self.location_tree = location_tree
        self.form_model = form_model

    def process_submission(self, submission_data):
        location_field_code = self._get_location_field_code()
        display_location = submission_data.get(location_field_code)
        if is_empty(display_location):
            return submission_data
        display_location_list = display_location.split(',')
        if len(display_location_list) > 1:
            submission_data[location_field_code] = display_location_list
            return submission_data
        lowest_level_location = display_location_list[0]
        location_hierarchy = self.location_tree.get_location_hierarchy(lowest_level_location)
        submission_data[location_field_code] = location_hierarchy
        return submission_data

    def _get_location_field_code(self):
        return self._get_field_code_by_name(LOCATION_TYPE_FIELD_NAME)

    def _get_field_code_by_name(self,field_name):
        field = self.form_model.get_field_by_name(name=field_name)
        return field.code if field is not None else None

    def _get_geo_field_code(self):
        fields = [field for field in self.form_model.fields if field.type.lower() == field_attributes.LOCATION_FIELD]
        return fields[0].code if len(fields) else None

    def _get_location_details(self, location_hierarchy):
        lowest_level_name = location_hierarchy[0]
        lowest_level = len(location_hierarchy) - 1
        return lowest_level, lowest_level_name

    def process_entity_creation(self,processed_cleaned_data):
        location_hierarchy = processed_cleaned_data.get(self._get_location_field_code(), None)
        geo_code = processed_cleaned_data.get(self._get_geo_field_code(), None)

        handler = self.get_hierarchy_geometry_handler(geo_code, location_hierarchy)
        return handler(geo_code,location_hierarchy)

    def get_hierarchy_geometry_handler(self,geo_code,location_hierarchy):
        if location_hierarchy is None and geo_code is None:
            return self.hierarchy_geometry_none_handler
        if location_hierarchy is not None and geo_code is None:
            return self.hierarchy_geometry_location_handler
        if geo_code is not None and location_hierarchy is None:
            return self.hierarchy_geometry_geo_code_handler
        return self.hierarchy_geometry_location_geo_code_handler

    def hierarchy_geometry_location_geo_code_handler(self, geo_code, location_hierarchy):
        return location_hierarchy, convert_to_geometry(geo_code)

    def hierarchy_geometry_geo_code_handler(self,geo_code,location_hierarchy):
        lat, long = geo_code
        location_hierarchy = self.location_tree.get_location_hierarchy_for_geocode(lat=lat,
            long=long)
        return location_hierarchy, convert_to_geometry(geo_code)


    def hierarchy_geometry_location_handler(self,geo_code,location_hierarchy):
        geometry = convert_to_geometry(self._get_geo_code_from_location_hierarchy(location_hierarchy))
        return location_hierarchy,geometry

    def hierarchy_geometry_none_handler(self,geo_code,location_hierarchy):
        return None,None

    def _get_geo_code_from_location_hierarchy(self, location_hierarchy):
        lowest_level, lowest_level_name = self._get_location_details(location_hierarchy)
        translated_long_lat_tuple = self.location_tree.get_centroid(lowest_level_name, lowest_level)
        return self._get_inverted_tuple(translated_long_lat_tuple) if translated_long_lat_tuple is not None else None

    def _get_inverted_tuple(self, tuple_to_be_inverted):
        return tuple_to_be_inverted[1], tuple_to_be_inverted[0]

