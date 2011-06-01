# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from mangrove.datastore.database import DatabaseManager, DataObject
from mangrove.datastore.documents import DataDictDocument
from mangrove.errors.MangroveException import DataObjectAlreadyExists, DataObjectNotFound
from mangrove.utils.types import is_string

# TODO: Temporary stuff, till datadict is fully implemented in datawinners : Aroj
def get_default_datadict_type():
    try:
        return get_datadict_type_by_slug(DatabaseManager(),"default")
    except DataObjectNotFound:
        d = DataDictType(DatabaseManager(), name='Default Datadict Type', slug='default', primitive_type='string')
        d.save()
        return d

def get_datadict_type(dbm, id):
    assert isinstance(dbm, DatabaseManager)
    return dbm.get(id, DataDictType)

def get_datadict_type_by_slug(dbm,slug):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(slug)

    rows = dbm.load_all_rows_in_view('by_datadict_type', key=slug,include_docs='true')
    if not len(rows):
        raise DataObjectNotFound("DataDictType","slug",slug)
    assert len(rows) == 1, "More than one item found for slug %s" % (slug,)

    #  include_docs = 'true' returns the doc as a dict, which has to be wrapped into a DataDictDocument, and then into a DataDictType
    _doc = DataDictDocument.wrap(rows[0].doc)
    return DataDictType.new_from_db(dbm,_doc)


def get_datadict_types(dbm, ids):
    assert isinstance(dbm, DatabaseManager)
    return dbm.get_many(ids, DataDictType)


def create_datadict_type(dbm, name, slug, primitive_type, description=None, constraints=None, tags=None):
    ddtype = DataDictType(dbm=dbm, name=name, slug=slug, primitive_type=primitive_type, description=description,
                          constraints=constraints, tags=tags)
    ddtype.save()
    return ddtype


def get_or_create_data_dict(dbm, name, slug, primitive_type, description=None, constraints=None, tags=None):
    try:
        return get_datadict_type_by_slug(dbm, slug)
    except DataObjectNotFound:
        pass
    return create_datadict_type(dbm, name, slug, primitive_type, description, constraints, tags)


class DataDictType(DataObject):
    '''DataDict is an abstraction that stores named data types and constraints .'''

    __document_class__ = DataDictDocument

    def __init__(self, dbm, name=None, slug=None, primitive_type=None, description=None, \
                 constraints=None, tags=None, id=None, **kwargs):

        '''Create a new DataDictType.

        This represents a type of data that can be used to coordinate data collection and interoperability.
        '''
        assert isinstance(dbm, DatabaseManager)
        assert name is None or is_string(name)
        assert slug is None or is_string(slug)
        assert primitive_type is None or is_string(primitive_type)
        assert description is None or is_string(description)
        assert constraints is None or isinstance(constraints, dict)
        # how to assert any kwargs?

        DataObject.__init__(self, dbm)

        # Are we being constructed from an existing doc?
        if name is None:
            return

        # Not made from existing doc, so create a new one
        doc = DataDictDocument(id, primitive_type, constraints, slug, name, description, tags, **kwargs)
        self._set_document(doc)

    @property
    def name(self):
        return self._doc.name

    @property
    def slug(self):
        return self._doc.slug

    @property
    def description(self):
        return self._doc.description

    @description.setter
    def description(self,value):
        self._doc.description = value

    @property
    def constraints(self):
        return self._doc.constraints

    @property
    def primitive_type(self):
        return self._doc.primitive_type

    @property
    def tags(self):
        return self._doc.tags

    def to_json(self):
        return self._doc.unwrap()

    @classmethod
    def create_from_json(cls, json,dbm):
        doc = DataDictDocument.wrap(json)
        return DataDictType.new_from_db(dbm,doc)

    def update_record_caches(self):
        '''This function will update the cached version of this type in all assosciated datarecords.'''
        rows = self._dbm.load_all_rows_in_view('datarecords_by_datatype_and_label', key=[self.id])
        records_to_update = [{'id': row.id, 'label': row['key'][1]} for row in rows]
        for record in records_to_update:
            doc = dbm.get(record['id'], DataRecord)
