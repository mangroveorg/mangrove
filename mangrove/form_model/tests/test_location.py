import unittest
from mock import Mock
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.field import HierarchyField
from mangrove.form_model.form_model import FormModel, LOCATION_TYPE_FIELD_NAME, LOCATION_TYPE_FIELD_CODE
from mangrove.form_model.location import Location

class TestLocation(unittest.TestCase):
    def setUp(self):
        self.lowest_level_location = 'pune'
        self.location = Location(self.location_hierarchy_stub, self.form())

    def test_should_not_do_anything_when_location_and_geo_is_not_present(self):
        submission={'name':'something'}
        self.assertEquals(submission,self.location.process_submission(submission))

    def test_should_convert_location_to_location_hierarchy(self):
        submission={LOCATION_TYPE_FIELD_CODE: self.lowest_level_location,'q':"sdasd"}
        augmented_submission={LOCATION_TYPE_FIELD_CODE:['india','mh','pune'],'q':"sdasd"}
        self.assertEquals(augmented_submission,self.location.process_submission(submission))

    def location_hierarchy_stub(self,lowest_level_location_name):
        if lowest_level_location_name=='pune':
            return ['india','mh','pune']

    def form(self):
        manager=Mock(spec=DatabaseManager)
        question4 = HierarchyField(name=LOCATION_TYPE_FIELD_NAME, code=LOCATION_TYPE_FIELD_CODE,
            label=LOCATION_TYPE_FIELD_NAME,ddtype=(Mock()))
        form_model = FormModel(manager, name="asd", form_code="asd", fields=[
            question4])
        return form_model