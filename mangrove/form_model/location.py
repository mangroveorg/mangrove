from mangrove.form_model.form_model import LOCATION_TYPE_FIELD_NAME

class Location(object):
    def __init__(self,get_location_heirarchy_from_name, form_model):
        self.get_location_heirarchy_from_name = get_location_heirarchy_from_name
        self.form_model = form_model

    def process_submission(self, submission_data):
        location_field_code = self._get_location_field_code()
        location_hierarchy = self.get_location_heirarchy_from_name(submission_data.get(location_field_code))
        submission_data[location_field_code] = location_hierarchy
        return submission_data

    def _get_location_field_code(self):
        return self._get_field_code_by_name(LOCATION_TYPE_FIELD_NAME)

    def _get_field_code_by_name(self,field_name):
        field = self.form_model.get_field_by_name(name=field_name)
        return field.code if field is not None else None


