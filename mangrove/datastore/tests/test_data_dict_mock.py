
from datetime import datetime
import unittest
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType, create_datadict_type, get_datadict_type_by_slug
from mangrove.errors.MangroveException import DataObjectNotFound


class TestDataDict(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        self.patcher = patch('mangrove.datastore.documents.utcnow')
        self.datetime_module = self.patcher.start()
        self.datetime_module.return_value = datetime(2010, 01, 01, 10, 11, 12)

    def tearDown(self):
        self.patcher.stop()

    def test_should_convert_to_json(self):
        _id = "1"
        name_type = DataDictType(self.dbm, name='First name', slug='first_Name', primitive_type='string', id=_id)
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

    def test_should_be_equal_if_json_presentation_are_the_same(self):
        _id = "1"
        dd1 = DataDictType(self.dbm, name='First name', slug='first_Name', primitive_type='string', id=_id)
        dd2 = DataDictType(self.dbm, name='First name', slug='first_Name', primitive_type='string', id=_id)

        self.assertTrue(dd2 == dd1)

    def test_should_be_not_equal_if_type_is_different(self):
        _id = "1"
        dd1 = DataDictType(self.dbm, name='First name', slug='first_Name', primitive_type='string', id=_id)
        dd2 = None

        self.assertFalse(dd2 == dd1)

    def test_should_be_not_equal_if_type_is_same_and_json_repr_are_not_same(self):
        _id = "1"
        dd1 = DataDictType(self.dbm, name='First name', slug='first_Name', primitive_type='string', id=_id)
        dd2 = DataDictType(self.dbm, name='Last name', slug='last_Name', primitive_type='string', id=_id)

        self.assertTrue(dd2 != dd1)

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

        ddtype = DataDictType.create_from_json(json, self.dbm)
        self.assertEqual(_id, ddtype.id)
        self.assertEqual(first_name, ddtype.name)
        self.assertEqual(primitive_type, ddtype.primitive_type)
        self.assertEqual(slug, ddtype.slug)
        self.assertEqual({}, ddtype.constraints)
        self.assertEqual([], ddtype.tags)

    def test_should_create_ddtype(self):
        NAME = 'Default Datadict Type'
        SLUG = 'default'
        TYPE = 'string'
        DESC = 'description'

        ddtype = create_datadict_type(self.dbm, name=NAME,
                                      slug=SLUG, primitive_type=TYPE, constraints={}, description=DESC)

        self.dbm._save_document.assert_called_once_with(ddtype._doc)

        self.assertEqual(NAME, ddtype.name)
        self.assertEqual(DESC, ddtype.description)
        self.assertEqual(SLUG, ddtype.slug)
        self.assertEqual(TYPE, ddtype.primitive_type)

    def test_should_throw_exception_if_slug_not_found(self):
        self.dbm.load_all_rows_in_view.return_value = []
        self.assertRaises(DataObjectNotFound, get_datadict_type_by_slug, self.dbm, "SLUG")

    def test_should_return_ddtype_by_slug(self):
        expected = DataDictType(self.dbm, "name", "slug", primitive_type="string")
        db_row = Mock()
        db_row.doc = expected._doc._data
        self.dbm.load_all_rows_in_view.return_value = [db_row]

        actual = get_datadict_type_by_slug(self.dbm, "slug")

        self.assertIsInstance(actual, DataDictType)
        self.assertEqual(expected.id, actual.id)
