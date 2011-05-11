# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import datetime
import unittest
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType


class TestDataDict(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.patcher = patch('mangrove.datastore.documents.utcnow')
        self.datetime_module = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_should_convert_to_json(self):
        self.datetime_module.return_value = datetime(2010,01,01,10,11,12)
        _id = "1"
        name_type = DataDictType(self.dbm, name='First name', slug='first_Name', primitive_type='string',id = _id)
        expected_json = {'_id': _id,
                         'constraints': {},
                         'created': '2010-01-01T10:11:12+00:00',
                         'description': None,
                         'document_type': u'DataDict',
                         'modified': None,
                         'name': u'First name',
                         'primitive_type': u'string',
                         'slug': u'first_Name',
                         'tags': [],
                         'void': False}
        self.assertEqual(expected_json, name_type.to_json())


    def test_should_create_from_json(self):
        self.datetime_module.return_value = datetime(2010,01,01,10,11,12)
        _id = "1"
        first_name = u'First name'
        primitive_type = u'string'
        slug = u'first_Name'
        json = {'_id': _id,
                         'constraints': {},
                         'created': '2010-01-01T10:11:12+00:00',
                         'description': None,
                         'document_type': u'DataDict',
                         'modified': None,
                         'name': first_name,
                         'primitive_type': primitive_type,
                         'slug': slug,
                         'tags': [],
                         'void': False}

        ddtype = DataDictType.create_from_json(json,self.dbm)
        self.assertEqual(_id,ddtype.id)
        self.assertEqual(first_name,ddtype.name)
        self.assertEqual(primitive_type,ddtype.primitive_type)
        self.assertEqual(slug,ddtype.slug)
        self.assertEqual({},ddtype.constraints)
        self.assertEqual([],ddtype.tags)
