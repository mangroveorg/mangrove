# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import copy
from datetime import datetime
from time import mktime
from collections import defaultdict

from documents import EntityDocument, DataRecordDocument, attributes
from datadict import DataDictType, get_datadict_types
import mangrove.datastore.aggregationtree as atree
from mangrove.errors.MangroveException import EntityTypeAlreadyDefined, EntityInstanceDoesNotExistsException
from mangrove.utils.types import is_empty
from mangrove.utils.types import is_not_empty, is_sequence, is_string
from mangrove.utils.dates import utcnow
from database import DatabaseManager

ENTITY_TYPE_TREE = '_entity_type'


def get_all_entity_types(dbm):
    assert isinstance(dbm, DatabaseManager)
    return atree.get_by_name(dbm, ENTITY_TYPE_TREE, get_or_create=True).get_paths()


def define_type(dbm, entity_type):
    assert is_not_empty(entity_type)

    type_path = ([entity_type] if is_string(entity_type) else entity_type)
    type_path = [item.strip() for item in type_path]

    # get the entity type aggregation tree, or create on if none-exists
    entity_tree = atree.get_by_name(dbm, ENTITY_TYPE_TREE, get_or_create=True)

    # types are all the paths in the tree
    entity_types = entity_tree.get_paths()

    if type_path in entity_types:
        raise EntityTypeAlreadyDefined("Type: %s is already defined" % '.'.join(entity_type))

    # now make the new one
    entity_tree.add_path([atree.AggregationTree.root_id] + entity_type)
    entity_tree.save()


def get_by_short_code(dbm, short_code):
    """
        Delegating to get by uuid for now.

    """
    return get(dbm, short_code)


def get(dbm, uuid):
    assert isinstance(dbm, DatabaseManager)
    entity_doc = dbm.load(uuid, EntityDocument)
    if entity_doc is not None:
        return Entity(dbm, _document=entity_doc)
    else:
        raise EntityInstanceDoesNotExistsException("Entity with id %s does not exist" % uuid)


def get_entities(dbm, uuids):
    return [get(dbm, i) for i in uuids]


def get_entities_by_type(dbm, entity_type):
    assert isinstance(dbm, DatabaseManager)
    assert is_string(entity_type)
    rows = dbm.load_all_rows_in_view('mangrove_views/by_type', key=entity_type)
    entities = [get(dbm, row['value']['_id']) for row in rows]
    return entities


def entities_for_attributes(attrs):
    '''
    retrieve entities with datarecords with the given
    named attributes. Can be used to search for entities
    by identifying info like a phone number

    Include 'type' as an attr to restrict to a given entity type

    returns a sequence of 0, 1 or more matches

    ex:
    attrs = { 'type':'clinic', 'name': 'HIV Clinic' }
    print entities_for_attributes(attrs)

    '''

    pass


# geo aggregation specific calls
def entities_near(geocode, radius=1, attrs=None):
    '''
    Retrieve an entity within the given radius (in kilometers) of
    the given geocode that matches the given attrs

    Include 'type' as an attr to restrict to a given entity type

    returns a sequence

    '''
    pass


def get_entities_in(dbm, geo_path, type_path=None):
    '''Retrieve an entity within the given fully-qualified geographic placename.'''
    assert isinstance(dbm, DatabaseManager)
    assert is_string(geo_path) or isinstance(geo_path, list)
    assert is_string(type_path) or isinstance(type_path, list) or type_path is None

    if is_string(geo_path):
        geo_path = [geo_path]
    if is_string(type_path):
        type_path = [type_path]

    entities = []

    # if type is unspecified, then return all entities
    if type_path is not None:
        # TODO: is the type field necessarily a heirarchy?
        # if not, then this needs to perform a query for each type and then take the intersection
        # of the result sets
        rows = dbm.load_all_rows_in_view('mangrove_views/by_type_geo', key=(type_path + geo_path))
        entities = [get(dbm, row.id) for row in rows]

    # otherwise, filter by type
    if type_path is None:
        rows = dbm.load_all_rows_in_view('mangrove_views/by_geo', key=geo_path)
        entities = [get(dbm, row.id) for row in rows]

    return entities


class Entity(object):
    """
    Entity class is main way of interacting with Entities AND datarecords.
    Datarecords are always submitted/retrieved from an Entity.
    """

    def __init__(self, dbm, entity_type=None, location=None, aggregation_paths=None,
                 geometry=None, centroid=None, gr_id=None, id=None, _document=None):
        '''Construct a new entity.

        Note: _couch_document is used for 'protected' factory methods and
        should not be passed in standard construction.

        If _couch_document is passed, the other args are ignored

        entity_type may be a string (flat type) or sequence (hierarchical type)
        '''
        assert isinstance(dbm, DatabaseManager)
        assert _document is not None or entity_type is None or is_sequence(entity_type) or is_string(entity_type)
        assert _document is not None or location is None or is_sequence(location)
        assert _document is not None or aggregation_paths is None or isinstance(aggregation_paths, dict)
        assert _document is not None or geometry is None or isinstance(geometry, dict)
        assert _document is not None or centroid is None or isinstance(centroid, list)
        assert _document is not None or gr_id is None or is_string(gr_id)
        assert _document is None or isinstance(_document, EntityDocument)

        self._dbm = dbm

        # Are we being constructed from an existing doc?
        if _document is not None:
            self._doc = _document
            return

        # Not made from existing doc, so create a new one
        self._doc = EntityDocument(id)

        # add aggregation paths
        if entity_type is not None:
            if is_string(entity_type):
                entity_type = entity_type.split(".")
            self._doc.entity_type = entity_type

        if location is not None:
            self._doc.location = location

        if geometry is not None:
            self._doc.geometry = geometry

        if centroid is not None:
            self._doc.centroid = centroid

        if gr_id is not None:
            self._doc.gr_id = gr_id

        if aggregation_paths is not None:
            reserved_names = (attributes.TYPE_PATH, attributes.GEO_PATH)
            for name in aggregation_paths.keys():
                if name in reserved_names:
                    raise ValueError('Attempted to add an aggregation path with a reserved name')
                self.set_aggregation_path(name, aggregation_paths[name])

        # TODO: why should Entities just be saved on init??

    def save(self):
        return self._dbm.save(self._doc).id

    @property
    def id(self):
        return self._doc.id

    @property
    def aggregation_paths(self):
        '''Returns a copy of the dict'''
#        return dict(self._doc.aggregation_paths)
        return copy.deepcopy(self._doc.aggregation_paths)

    @property
    def type_path(self):
        '''Returns a copy of the path'''
        return list(self._doc.entity_type)

    @property
    def location_path(self):
        '''Returns a copy of the path'''
        return list(self._doc.location)

    @property
    def type_string(self):
        p = self.type_path
        return ('' if p is None else '.'.join(p))

    @property
    def location_string(self):
        p = self.location_path
        return ('' if p is None else '.'.join(p))

    def set_aggregation_path(self, name, path):
        assert self._doc is not None
        assert is_string(name) and is_not_empty(name)
        assert is_sequence(path) and is_not_empty(path)

        assert isinstance(self._doc[attributes.AGG_PATHS], dict)
        self._doc[attributes.AGG_PATHS][name] = list(path)

        # TODO: Depending on implementation we will need to update aggregation paths
        # on data records--in which case we need to set a dirty flag and handle this
        # in save

    def add_data(self, data=(), event_time=None, submission_id=None):
        '''Add a new datarecord to this Entity and return a UUID for the datarecord.

        Arguments:
        data -- a sequence of ordered tuples, (label, value, type) where type is a DataDictType
        submission_id -- an id to a 'submission' document in the submission log from which
                        this data came
        event_time -- the time at which the event occured rather than when it was reported

        This is stored in couch as:
            submission_id = "..."
            event_time = "..."
            data: [
                            { 'type': <DataDictDocument>,'value': x},
                            ...
                        ]
        '''
        assert is_sequence(data)
        assert event_time is None or isinstance(event_time, datetime)
        assert self.id is not None  # should never be none, even if haven't been saved, should have a UUID
        # TODO: should we have a flag that says that this has been saved at least once to avoid adding data
        # records for an Entity that may never be saved? Should docs just be saved on init?
        if event_time is None:
            event_time = utcnow()

        data_list = []
        for (label, value, dd_type) in data:
            if not isinstance(dd_type, DataDictType) or is_empty(label):
                raise ValueError('Data must be of the form (label, value, DataDictType).')
            data_list.append((label, dd_type, value))

        data_record_doc = DataRecordDocument(entity_doc=self._doc, event_time=event_time,
                                             data=data_list, submission_id=submission_id)
        return self._dbm.save(data_record_doc).id

    def invalidate_data(self, uid):
        '''Mark datarecord identified by uid as 'invalid'.

        Can be used to mark a submitted record as 'bad' so that
        it will be ignored in reporting. This is because we
        don't want to delete submitted data, even if it is
        erroneous.
        '''
        self._dbm.invalidate(uid)

    def invalidate(self):
        '''Mark the entity as invalid.

        This will also mark all associated data records as invalid.
        '''
        self._doc.void = True
        self.save()
        for id in self._get_data_ids():
            self.invalidate_data(id)

    def _get_data_ids(self):
        '''Returns a list of all data documents ids for this entity.

        This should only be used internally to perform update actions on data records as necessary.
        '''
        rows = self._get_rows()
        return [row['value']['_id'] for row in rows]

    def _get_rows(self):
        """
        Return a list of all the data records associated with this
        entity.
        """
        return self._dbm.load_all_rows_in_view('mangrove_views/entity_data', key=self.id)
        
    def get_all_data(self):
        """
        Return a dict where the first level of keys is the event time,
        the second level is the data dict type slug, and the third
        contains the data type, value, and label of the data record.
        """
        result = defaultdict(dict)
        for row in self._get_rows():
            event_time = row['value'][u'event_time']
            data_keys = row['value']['data'].keys()
            assert len(data_keys)==1
            label = data_keys[0]
            value = row['value']['data'][label][u'value']
            data_type = row['value']['data'][label]['type']
            result[event_time][data_type['slug']] = {
                u'type': data_type,
                u'value': value,
                u'label': label,
                }
        return result

    def data_types(self, tags=None):
        '''Returns a list of each type of data that is stored on this entity.'''
        assert tags is None or isinstance(tags, list) or is_string(tags)
        result = []
        if tags is None or is_empty(tags):
            rows = self._dbm.load_all_rows_in_view('mangrove_views/entity_datatypes', key=self.id)
            result = get_datadict_types(self._dbm, [row['value'] for row in rows])
        else:
            if is_string(tags):
                tags = [tags]
            keys = []
            for tag in tags:
                rows = self._dbm.load_all_rows_in_view('mangrove_views/entity_datatypes_by_tag', key=[self.id, tag])
                keys.append([row['value'] for row in rows])
            ids_with_all_tags = list(set.intersection(*map(set, keys)))
            result = get_datadict_types(self._dbm, ids_with_all_tags)
        return result

    def state(self):
        '''Returns a dictionary containing the current state of the entity.

        Contains the latest value of each type of data stored on the entity.
        '''
        pass

    def values(self, aggregation_rules, asof=None):
        """
        returns the aggregated value for the given fields using the aggregation function specified for data collected till a point in time.
        Eg: data_records_func = {'arv':'latest', 'num_patients':'sum'} will return latest value for ARV and sum of number of patients
        """
        asof = asof or utcnow()
        result = {}
        for field, aggregate_fn in aggregation_rules.items():
            view_name = self._translate(aggregate_fn)
            result[field] = self._get_aggregate_value(field, view_name, asof)
        return result

    def _get_aggregate_value(self, field, aggregate_fn, date):
        entity_id = self._doc.id
        time_since_epoch_of_date = int(mktime(date.timetuple())) * 1000
        rows = self._dbm.load_all_rows_in_view('mangrove_views/' + aggregate_fn, group_level=3, descending=False,
                                                     startkey=[self.type_path, entity_id, field],
                                                     endkey=[self.type_path, entity_id, field, time_since_epoch_of_date])
        # The above will return rows in the format described:
        # Row key=['clinic', 'e4540e0ae93042f4b583b54b6fa7d77a'],
        #   value={'beds': {'timestamp_for_view': 1420070400000, 'value': '15'},
        #           'entity_id': {'value': 'e4540e0ae93042f4b583b54b6fa7d77a'}, 'document_type': {'value': 'Entity'},
        #           'arv': {'timestamp_for_view': 1420070400000, 'value': '100'}, 'entity_type': {'value': 'clinic'}
        #           }
        #  The aggregation map-reduce view will return only one row for an entity-id
        # From this we return the field we are interested in.
        # TODO: Hardcoding to 'latest' for now. Generalize to any aggregation function.
        return rows[0]['value']['latest'] if len(rows) else None

    def _translate(self, aggregate_fn):
        view_names = {"latest": "by_values"}
        return (view_names[aggregate_fn] if aggregate_fn in view_names else aggregate_fn)
