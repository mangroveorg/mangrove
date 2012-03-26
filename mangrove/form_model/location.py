from mangrove.form_model.form_model import LOCATION_TYPE_FIELD_NAME, LOCATION_TYPE_FIELD_CODE, GEO_CODE, GEO_CODE_FIELD_NAME
from mangrove.utils.geo_utils import convert_to_geometry

class Location(object):
    def __init__(self,location_tree, form_model):
        self.location_tree = location_tree
        self.form_model = form_model

    def process_submission(self, submission_data):
        location_field_code = self._get_location_field_code()
        location_hierarchy = self.location_tree.location_hierarchy_for_name(submission_data.get(location_field_code))
        submission_data[location_field_code] = location_hierarchy
        return submission_data

    def _get_location_field_code(self):
        return self._get_field_code_by_name(LOCATION_TYPE_FIELD_NAME)

    def _get_field_code_by_name(self,field_name):
        field = self.form_model.get_field_by_name(name=field_name)
        return field.code if field is not None else None

    def _get_geo_field_code(self):
        return self._get_field_code_by_name(GEO_CODE_FIELD_NAME)

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

    def hierarchy_geometry_geo_code_handler(self,geo_code,location_hierarchy):
        lat_string, long_string = tuple(geo_code.split())
        location_hierarchy = self.location_tree.get_location_hierarchy_for_geocode(lat=float(lat_string),
            long=float(long_string))
        geometry = convert_to_geometry((float(long_string),float(lat_string)))
        return location_hierarchy, geometry


    def hierarchy_geometry_location_handler(self,geo_code,location_hierarchy):
        lowest_level, lowest_level_name = self._get_location_details(location_hierarchy)
        translated_geo_code = self.location_tree.get_centroid(lowest_level_name, lowest_level)
        geometry = convert_to_geometry(tuple(translated_geo_code))
        return location_hierarchy,geometry


    def hierarchy_geometry_none_handler(self,geo_code,location_hierarchy):
        return None,None


