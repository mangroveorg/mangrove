# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from mangrove.datastore.documents import DocumentBase
from mangrove.datastore.entity import EntityDocument
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
import unittest


class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        self.database_manager = get_db_manager('http://localhost:5984/', 'mangrove-test')

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.database_manager)

    def test_should_create_database_if_it_does_not_exist(self):
        _delete_db_and_remove_db_manager(self.database_manager)
        server = 'http://localhost:5984/'
        database = 'mangrove-test'
        self.database_manager = get_db_manager(server, database)
        self.assertTrue(self.database_manager.url == server)
        self.assertTrue(self.database_manager.database_name == database)
        self.assertTrue(self.database_manager.server)
        self.assertTrue(self.database_manager.database)

    def test_should_persist_and_load_document_to_database(self):
        document = DocumentBase(document_type='TestDocument')
        id = self.database_manager._save_document(document)
        document = self.database_manager._load_document(id)
        self.assertTrue(document.document_type == 'TestDocument')

        document1 = self.database_manager._load_document(document.id)
        self.assertTrue(document1)

    def test_should_return_none_if_documentid_is_empty(self):
        self.assertIsNone(self.database_manager._load_document('', EntityDocument))

    def test_should_return_none_if_no_document_for_id(self):
        self.assertIsNone(self.database_manager._load_document('123abc', EntityDocument))
