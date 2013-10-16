
import unittest
from mangrove.datastore.datadict import create_datadict_type, get_datadict_type_by_slug, get_datadict_type
from mangrove.errors.MangroveException import  DataObjectNotFound
from mangrove.utils.test_utils.database_utils import create_dbmanager_for_ut, uniq


class TestDataDict(unittest.TestCase):

    def setUp(cls):
        create_dbmanager_for_ut(cls)

    def test_should_create_load_edit_datadict(self):
        SLUG_NAME = uniq('first_name')

        name_type = create_datadict_type(self.manager, name='First name', slug=SLUG_NAME, primitive_type='string')

        saved_type = get_datadict_type(self.manager, name_type.id)
        self.assertEqual(name_type.id, saved_type.id)
        self.assertEqual(name_type.slug, saved_type.slug)

        ddtype = get_datadict_type_by_slug(self.manager, slug=SLUG_NAME)

        self.assertEqual(name_type.id, ddtype.id)
        self.assertEqual(name_type.slug, ddtype.slug)

        ddtype.description = "new desc"
        ddtype.save()

        saved = get_datadict_type_by_slug(self.manager, slug=SLUG_NAME)
        self.assertEqual("new desc", saved.description)

    def test_should_raise_exception_if_datadict_not_found(self):
        with self.assertRaises(DataObjectNotFound):
            get_datadict_type(self.manager, "ID not in db")

if __name__ == '__main__':
    unittest.main()