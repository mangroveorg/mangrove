TEST_LAT=60
TEST_LONG=-12
TEST_LOCATION_HIERARCHY_FOR_GEO_CODE=['madagascar']

class DummyLocationTree(object):
    def get_location_hierarchy_for_geocode(self, lat, long ):
        return TEST_LOCATION_HIERARCHY_FOR_GEO_CODE

    def get_centroid(self, location_name, level):
        return TEST_LAT, TEST_LONG

    def location_hierarchy_for_name(self,lowest_level_location_name):
        if lowest_level_location_name=='pune':
            return ['india','mh','pune']

