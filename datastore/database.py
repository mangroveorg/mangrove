# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from couchdb.design import ViewDefinition
from settings import *
from couchdb.http import ResourceNotFound
from threading import Lock
import config
from documents import DocumentBase
import couchdb.client
from datetime import datetime
from ..utils import dates
import views


_dbms = {}


def get_db_manager(server=None, database=None):
    global _dbms
    assert _dbms is not None

    # use defaults if not passed
    srv = (server if server is not None else config._server)
    db = (database if database is not None else config._db)
    k = (srv, db)
    # check if already created and in dict
    if k not in _dbms or _dbms[k] is None:
        with Lock():
            if k not in _dbms or _dbms[k] is None:
                # nope, create it
                _dbms[k] = DatabaseManager(server, database)

    return _dbms[k]


def remove_db_manager(dbm):
    global _dbms
    assert isinstance(dbm, DatabaseManager)
    assert dbm in _dbms.values()

    with Lock():
        try:
            del _dbms[(dbm.url, dbm.database_name)]
        except KeyError:
            pass  # must have been already deleted


def _delete_db_and_remove_db_manager(dbm):
    '''This is really only used for testing puropses.'''
    del dbm.server[dbm.database_name]
    remove_db_manager(dbm)


class DatabaseManager(object):
    def __init__(self, server=None, database=None):
        """
            Connect to the CouchDB server. If no database name is given , use the name provided in the settings
        """
        self.url = (server if server is not None else SERVER)
        self.database_name = database or DATABASE
        self.server = couchdb.client.Server(self.url)
        try:
            self.database = self.server[self.database_name]
        except ResourceNotFound:
            self.database = self.server.create(self.database_name)

        if self.database is not None:
            self.create_default_views()

    def __unicode__(self):
        return u"Connected on %s - working on %s" % (self.url, self.database_name)

    def __str__(self):
        return unicode(self)

    def __repr__(self):
        return repr(self.database)

    def load_all_rows_in_view(self, view_name, **values):
        return self.database.view(view_name, **values).rows

    def create_view(self, view_name, map, reduce, view_document='mangrove_views'):
        view = ViewDefinition(view_document, view_name, map, reduce)
        view.sync(self.database)

    def create_default_views(self):
        views.create_views(self)

    def save(self, document, modified=None):
        assert modified is None or isinstance(modified, datetime)
        document.modified = (modified if modified is not None else dates.utcnow())
        document.store(self.database)
        return document

    def invalidate(self, uid):
        doc = self.load(uid)
        doc.void = True
        self.save(doc)

    def delete(self, document):
        self.database.delete(document)

    def load(self, id, document_class=DocumentBase):
        if id:
            return document_class.load(self.database, id=id)
        return None
