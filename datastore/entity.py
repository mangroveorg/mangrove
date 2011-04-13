# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import copy
from datetime import datetime
from documents import EntityDocument, DataRecordDocument, attributes
from ..utils.types import is_not_empty, is_sequence, is_string, primitive_type
from ..utils.dates import utcnow
from database import DatabaseManager

def get(dbm, uuid):
    assert isinstance(dbm, DatabaseManager)
    entity_doc = dbm.load(uuid, EntityDocument)
    e = Entity(dbm, _document = entity_doc)
    return e

def get_entities(dbm, uuids):
    return [ get(dbm, i) for i in uuids ]

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

def entities_in(geoname, attrs=None):
    '''
    Retrieve an entity within the given fully-qualified geographic
    placename.

    Include 'type' as an attr to restrict to a given entity type

    returns a sequence

    ex.
    found = entities_in(
    [us,ca,sanfrancisco],
    {'type':'patient', 'phone':'4155551212'}
    )

    '''
    pass


#
# Constants
#



# Entity class is main way of interacting with Entities AND datarecords.
# Datarecords are always submitted/retrieved from an Entity




class Entity(object):
    """
        Entity class is main way of interacting with Entities AND datarecords.
    """

    def __init__(self, dbm, entity_type = None,location=None, aggregation_paths = None, _document = None):
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
        assert _document is None or isinstance(_document, EntityDocument)

        self._dbm = dbm

        # Are we being constructed from an existing doc?
        if _document is not None:
            self._doc = _document
            return

        # Not made from existing doc, so create a new one
        self._doc = EntityDocument()

        # add aggregation paths
        if entity_type is not None:
            if is_string(entity_type):
                entity_type = entity_type.split(".")
            self._doc.entity_type = entity_type

        if location is not None:
            self._doc.location = location

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
        self._doc[attributes.AGG_PATHS][name]=list(path)

        # TODO: Depending on implementation we will need to update aggregation paths
        # on data records--in which case we need to set a dirty flag and handle this
        # in save

    def add_data(self, data = (), event_time = None, submission_id = None):
        '''Add a new datarecord to this Entity and return a UUID for the datarecord.

        Arguments:
        data -- a sequence of n-tuples in form of (key, value, <optional type>)
                e.g. [('name','bob','string'), ('age',20,'numeric')]
        submission_id -- an id to a 'submission' document in the submission log from which
                        this data came
        event_time -- the time at which the event occured rather than when it was reported

        This is stored in couch as:
            submission_id = "..."
            event_time = "..."
            attributes: {
                            'name': {
                                'value': 'bob',
                                'type': 'string'
                            },
                            'age': {
                                'value': '20',
                                'type': 'numeric'
                            },
                        }
        '''
        assert is_sequence(data)
        assert event_time is None or isinstance(event_time, datetime)
        assert self.id is not None # should never be none, even if haven't been saved, should have a UUID
        # TODO: should we have a flag that says that this has been saved at least once to avoid adding data
        # records for an Entity that may never be saved? Should docs just be saved on init?
        if event_time is None:
            event_time = utcnow()
            
        data_dict = {}
        for d in data:
            if len(d)<2 or len(d)>3:
                raise ValueError('data for a data record must be tuple of (name, value) or triple of (name,value,type)')

            name = d[0]
            value = d[1]
            typ = d[2] if len(d)==3 else primitive_type(value)
            data_dict[name] = { 'value': value, 'type': typ }

        data_record_doc = DataRecordDocument(entity_doc = self._doc, event_time = event_time,
                                             data = data_dict, submission_id = submission_id)
        return self._dbm.save(data_record_doc).id

    # Note: The below has not been implemented yet.
  	 	
  	 	
    def invalidate_data(self, uid):
  	 	
        '''
        Mark datarecord identified by uid as 'invalid'.

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
        rows = self._dbm.load_all_rows_in_view('mangrove_views/entity_data')
        return [row['value'] for row in rows]

    def values(self, aggregation_rules, asof = None):
        """
        returns the aggregated value for the given fields using the aggregation function specified for data collected till a point in time.
         Eg: data_records_func = {'arv':'latest', 'num_patients':'sum'} will return latest value for ARV and sum of number of patients
        """
        asof = asof or utcnow()
        result = {}
        
        for field,aggregate_fn in aggregation_rules.items():
            view_name = self._translate(aggregate_fn)
            result[field] = self._get_aggregate_value(field,view_name,asof)
        return result


    def _get_aggregate_value(self, field, aggregate_fn,date):
        entity_id = self._doc.id
        rows = self._dbm.load_all_rows_in_view('mangrove_views/'+aggregate_fn, group_level=3,descending=False,
                                                     startkey=[self.type_path, entity_id, field],
                                                     endkey=[self.type_path, entity_id, field, date.year, date.month, date.day, {}])
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
        view_names = { "latest" : "by_values" }
        return (view_names[aggregate_fn] if aggregate_fn in view_names else aggregate_fn)





    




    
