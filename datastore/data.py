# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from documents import attributes

BY_VALUES_ENTITY_ID_INDEX = 1
BY_VALUES_FIELD_INDEX = BY_VALUES_ENTITY_ID_INDEX + 1

class reduce_functions(object):
    '''Constants for referencing reduce functions. '''
    SUM = "sum"
    LATEST = "latest"
    COUNT = "count"  # Returns number of records containing the field

    SUPPORTED_FUNCTIONS = [SUM, LATEST, COUNT]

def _get_key_strategy(aggregate_on):
    if aggregate_on.get('type'):
        def _aggregate_by_path(db_key):
            entity_type,aggregation_type,field = db_key[:3]
            path = db_key[3:]
            key = tuple(path)
            return key,field

        return _aggregate_by_path
    else:
        def _aggregate_by_entity(db_key):
            key = db_key[BY_VALUES_ENTITY_ID_INDEX]
            field = db_key[BY_VALUES_FIELD_INDEX]
            return key, field

        return _aggregate_by_entity

def fetch(dbm, entity_type, aggregates=None, aggregate_on=None, starttime=None, endtime=None, filter=None):
    result = {}
    aggregates = {} if aggregates is None else aggregates
    aggregate_on = {} if aggregate_on is None else aggregate_on
    if aggregate_on:
        values = _load_all_fields_by_aggregation_path(dbm, entity_type, aggregate_on)
    else:
        values = _load_all_fields_aggregated(dbm, entity_type)

    interested_keys = None
    if filter:
        location = filter.get("location")
        assert location, "Only filter by location supported"
        if aggregate_on:
            interested_keys = [tuple(location)]
        else:
            interested_keys = _get_entities_for_location(dbm,entity_type, location)

    _parse_key = _get_key_strategy(aggregate_on)

    for key,val in values:
        result_key,field = _parse_key(key)
        if filter and result_key not in interested_keys:
            continue
        interested_aggregate = None
        if field in aggregates:
            interested_aggregate = aggregates.get(field)
        #        * overrides field specific aggregation, returns the aggregation for all fields.
        if "*" in aggregates:
            interested_aggregate = aggregates.get("*")
        if interested_aggregate:
            result.setdefault(result_key, {})[field] = val[interested_aggregate]
    return result

def _load_all_fields_aggregated(dbm, type_path):
    view_name = "by_values"
    startkey = [type_path]
    endkey = [type_path, {}]
    view_group_level = BY_VALUES_FIELD_INDEX + 1
    rows = dbm.load_all_rows_in_view('mangrove_views/' + view_name, group_level=view_group_level,
                                     startkey=startkey,
                                     endkey=endkey)
    values = []
    for row in rows:
        values.append((row.key,row.value))
    return values

def _load_all_fields_by_aggregation_path(dbm, entity_type, aggregate_on):
    view_name = "by_aggregation_path"
    aggregation_type = _translate_aggregation_type(aggregate_on)
    rows = dbm.load_all_rows_in_view('mangrove_views/' + view_name, group_level=aggregate_on['level'] + 3,
                                     startkey=[entity_type, aggregation_type],
                                     endkey=[entity_type, aggregation_type, {}])
    values = []
    for row in rows:
        values.append((row.key,row.value))
    return values

def _translate_aggregation_type(aggregate_on):
    AGGREGATE_ON_MAP = {'location': attributes.GEO_PATH}
    aggregate_on_type = aggregate_on['type']
    return AGGREGATE_ON_MAP[aggregate_on_type] if aggregate_on_type in AGGREGATE_ON_MAP else aggregate_on_type

def _get_entities_for_location(dbm,entity_type,location):
    view_name = "by_location"
    rows = dbm.load_all_rows_in_view('mangrove_views/' + view_name, reduce = False,
                                         startkey=[entity_type, location],
                                         endkey=[entity_type, location, {}])
    values = []
    for row in rows:
        values.append(row.value)
    return values
