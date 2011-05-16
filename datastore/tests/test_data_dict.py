# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import datetime
import unittest
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType, create_ddtype, get_datadict_type_by_slug
from mangrove.errors.MangroveException import DataObjectNotFound, DataObjectAlreadyExists


class TestDataDict(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.patcher = patch('mangrove.datastore.documents.utcnow')
        self.datetime_module = self.patcher.start()
        self.datetime_module.return_value = datetime(2010,01,01,10,11,12)

    def tearDown(self):
        self.patcher.stop()

    def test_should_convert_to_json(self):
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


    def test_should_create_ddtype(self):
        NAME = 'Default Datadict Type'
        SLUG = 'default'
        TYPE = 'string'
        DESC = 'description'

        with patch("mangrove.datastore.datadict.get_datadict_type_by_slug") as get_datadict_type_by_slug_mocked:
            get_datadict_type_by_slug_mocked.side_effect = DataObjectNotFound("DataDictType","slug",SLUG)
            ddtype = create_ddtype(self.dbm, name=NAME,
                                          slug=SLUG, primitive_type=TYPE,constraints={}, description=DESC)

            get_datadict_type_by_slug_mocked.assert_called_once_with(self.dbm,SLUG)
            self.dbm.save.assert_called_once_with(ddtype)

            self.assertEqual(NAME,ddtype.name)
            self.assertEqual(DESC,ddtype.description)
            self.assertEqual(SLUG,ddtype.slug)
            self.assertEqual(TYPE,ddtype.primitive_type)

    def test_should_not_create_ddtype_if_slug_exists(self):
        NAME = 'Default Datadict Type'
        SLUG = 'default'
        TYPE = 'string'
        DESC = 'description'

        with patch("mangrove.datastore.datadict.get_datadict_type_by_slug") as get_datadict_type_by_slug_mocked:
            get_datadict_type_by_slug_mocked.return_value = Mock(spec=DataDictType)
            try:
                ddtype = DataDictType(self.dbm, name=NAME,
                                          slug=SLUG, primitive_type=TYPE,constraints={}, description=DESC)
                ddtype.save()
                self.fail("Expected DataObjectAlreadyExists exception")
            except DataObjectAlreadyExists:
                pass
            self.assertEqual(0,self.dbm.save.call_count)


    def test_should_throw_exception_if_slug_not_found(self):
        self.dbm.load_all_rows_in_view.return_value = []
        self.assertRaises(DataObjectNotFound,get_datadict_type_by_slug,self.dbm,"SLUG")

    def test_should_return_ddtype_by_slug(self):
        expected = DataDictType(self.dbm,"name","slug",primitive_type="string")
        db_row = Mock()
        db_row.doc = expected._doc._data
        self.dbm.load_all_rows_in_view.return_value = [ db_row ]

        actual = get_datadict_type_by_slug(self.dbm, "slug")

        self.assertIsInstance(actual,DataDictType)
        self.assertEqual(expected.id, actual.id)

