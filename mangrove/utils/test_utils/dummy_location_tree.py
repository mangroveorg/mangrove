TEST_LAT=-12
TEST_LONG=60
TEST_LOCATION_HIERARCHY_FOR_GEO_CODE=['madagascar']

class DummyLocationTree(object):
    def get_location_hierarchy_for_geocode(self, lat, long ):
        return TEST_LOCATION_HIERARCHY_FOR_GEO_CODE

    def get_centroid(self, location_name, level):
        if location_name=="jalgaon" and level==2:
            return None
        return TEST_LONG, TEST_LAT

    def get_location_hierarchy(self,lowest_level_location_name):
        if lowest_level_location_name=='pune':
            return ['pune','mh','india']

