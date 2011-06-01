# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.datadict import create_datadict_type, get_datadict_type_by_slug, get_datadict_type
from mangrove.errors.MangroveException import DataObjectAlreadyExists, DataObjectNotFound


class TestDataDict(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def test_should_create_load_edit_datadict(self):
        FIRST_NAME_SLUG = 'first_name'

        name_type = create_datadict_type(self.dbm, name='First name', slug=FIRST_NAME_SLUG, primitive_type='string')

        saved_type = get_datadict_type(self.dbm, name_type.id)
        self.assertEqual(name_type.id, saved_type.id)
        self.assertEqual(name_type.slug, saved_type.slug)

        ddtype = get_datadict_type_by_slug(self.dbm, slug=FIRST_NAME_SLUG)

        self.assertEqual(name_type.id, ddtype.id)
        self.assertEqual(name_type.slug, ddtype.slug)

        ddtype.description = "new desc"
        ddtype.save()

        saved = get_datadict_type_by_slug(self.dbm, slug=FIRST_NAME_SLUG)
        self.assertEqual("new desc", saved.description)

    def test_should_raise_exception_if_datadict_not_found(self):
        with self.assertRaises(DataObjectNotFound):
            get_datadict_type(self.dbm, "ID not in db")
