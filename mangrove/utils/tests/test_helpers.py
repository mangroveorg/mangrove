from unittest  import TestCase
from mangrove.utils.helpers import find_index_represented

class TestIndexFinder(TestCase):
    def setUp(self):
        pass

    def test_encode_decode(self):
        self.assertEqual(55, find_index_represented("2d"))
  