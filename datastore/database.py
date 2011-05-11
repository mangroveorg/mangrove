# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from threading import Lock

from couchdb.design import ViewDefinition
from couchdb.http import ResourceNotFound
import couchdb.client

from settings import *
import config
from documents import DocumentBase
from datetime import datetime
from mangrove.utils import dates
from mangrove.utils.types import is_empty, is_sequence
from mangrove.errors.MangroveException import NoDocumentError, ObjectNotFound
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
    '''This is really only used for testing purposes.'''
    if dbm.database_name in dbm.server:
        del dbm.server[dbm.database_name]
    remove_db_manager(dbm)


class DataObject(object):
    '''
    Superclass for all objects that are essentially wrappers of DB data.

    There isn't much API contract that needs to be implemented by subclasses:
    - They must have a class level member called __document_class__ that points to the python-couchdb
       document class that they use internally.

    - A constructor where only 'dbm' is required (for initial construction)

    - _set_document call which is used to initialize with a new python-couchdb document

    - a member self._doc which is used to hold the python-couchdb document

    '''

    __document_class__ = None

    @classmethod
    def new_from_db(cls, dbm, doc):
        assert isinstance(doc, cls.__document_class__)
        me = cls(dbm)
        me._set_document(doc)
        return me

    @classmethod
    def get(cls, dbm, id):
        return dbm.get(id, cls)

    def __init__(self, dbm):
        self._doc = None
        self._dbm = dbm

    def _set_document(self, document):
        assert isinstance(document, self.__document_class__)
        self._doc = document

    def save(self):
        if self._doc is None:
            raise NoDocumentError('No document to save')

        return self._dbm.save(self)

    def delete(self):
        self._dbm.delete(self)

    @property
    def id(self):
        return (self._doc.id if self._doc is not None else None)



class DatabaseManager(object):
    def __init__(self, server=None, database=None):
        """
            Connect to the CouchDB server. If no database name is given , use the name provided in the settings
        """
        self.cache_lock = Lock()
        self.doc_cache = {}
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

    def blow_cache(self):
        '''
        The DBM holds an in memory document cache where it stores documents after retrieval
        from Couch.

        This blows the cache, removing references to in-memory documents.

        NOTE: If an object holds an external reference to the document, it will stay around
        in memory, but a new document will be returned if requested from the DBM

        '''
        with self.cache_lock:
            self.doc_cache = {}
            
    def load_all_rows_in_view(self, view_name, **values):
        return self.database.view(view_name, **values).rows

    def create_view(self, view_name, map, reduce, view_document='mangrove_views'):
        view = ViewDefinition(view_document, view_name, map, reduce)
        view.sync(self.database)

    def create_default_views(self):
        views.create_views(self)

    def _save_document(self, document, modified=None):
        assert modified is None or isinstance(modified, datetime)
        document.modified = (modified if modified is not None else dates.utcnow())
        document.store(self.database)
        return document

    def invalidate(self, uid):
        doc = self._load_document(uid)
        doc.void = True
        self._save_document(doc)

    def _delete_document(self, document):
        self.database.delete(document)

    def _load_document(self, id, document_class=DocumentBase):
        '''
        Load a document from the DB into an in memory document object.

        Low level interface does not create wrapping DataObject or put in cache

        '''
        if is_empty(id):
            return None
        else:
            return document_class.load(self.database, id=id)

    def get_many(self, ids, object_class, get_or_create=False, force_reload=False):
        '''
        Get many data objects at once.

        Returns a (possibly empty) list of retrieved objects
        
        '''
        assert is_sequence(ids)
        objs = []
        for id in ids:
            try:
                objs.append(self.get(id, object_class, get_or_create, force_reload))
            except ObjectNotFound:
                pass
        return objs

    def get(self, id, object_class, get_or_create=False, force_reload=False):
        '''
        Higher level call for retrieving not just the CouchDB document but
        creating the full API object that wraps it.

        '''
        assert issubclass(object_class, DataObject)


        obj = None

        if force_reload or id not in self.doc_cache:
            doc = self._load_document(id, object_class.__document_class__)

            if doc is None and not get_or_create:
                raise ObjectNotFound(id)
            elif doc is None:
                # didn't find it, but get_or_create is True, so
                # lets make it
                doc = object_class.__document_class__(id=id)
                doc = doc.store(self.database)

            obj = object_class.new_from_db(self, doc)
            with self.cache_lock:
                self.doc_cache[obj._doc.id] = obj
        elif not force_reload:
            # id was in cache, Lock, dble check, return
            with self.cache_lock:
                # slight chance race condition blew it away, so check
                if id in self.doc_cache:
                    obj = self.doc_cache[id]
        return obj

    def save(self, d_obj):
        assert isinstance(d_obj, DataObject)
        assert d_obj._doc is not None

        with self.cache_lock:
            self.doc_cache[d_obj._doc.id] = d_obj

        return d_obj._doc.store(self.database).id

    def delete(self, d_obj):
        '''
        Deletes the document associated with the data_obj from the database and
        removes from the cache.

        '''
        assert isinstance(d_obj, DataObject)

        if d_obj._doc is None:
            raise NoDocumentError

        id = d_obj._doc.id
        self.database.delete(d_obj._doc)
        with self.cache_lock:
            if id in self.doc_cache:
                del self.doc_cache[id]