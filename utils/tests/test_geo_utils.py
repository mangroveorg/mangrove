# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.utils.geo_utils import convert_to_geometry

class TestGeoUtils(unittest.TestCase):
    def test_should_convert_lat_long_to_geometry(self):
        lat = 19
        long = 91
        geometry = convert_to_geometry((lat, long))
        self.assertEqual(geometry['Type'],'Point')
        self.assertEqual(geometry['coordinates'],[lat,long])

    def test_should_return_none_for_empty_values(self):
        geometry = convert_to_geometry(None)
        self.assertTrue(geometry is None)

