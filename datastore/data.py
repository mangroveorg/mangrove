# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from documents import attributes
from mangrove.errors.MangroveException import AggregationNotSupportedForTypeException

BY_VALUES_ENTITY_ID_INDEX = 1
BY_VALUES_FIELD_INDEX = BY_VALUES_ENTITY_ID_INDEX + 1
BY_VALUES_FORM_CODE_INDEX = BY_VALUES_FIELD_INDEX + 1

class reduce_functions(object):
    '''Constants for referencing reduce functions. '''
    SUM = "sum"
    LATEST = "latest"
    COUNT = "count"  # Returns number of records containing the field
    AVG = 'avg'
    MIN = 'min'
    MAX = 'max'

    SUPPORTED_FUNCTIONS = [SUM, LATEST, COUNT, AVG, MIN, MAX]


def _get_key_strategy(aggregate_on, filter):
    if aggregate_on.get('type'):
        def _aggregate_by_path(db_key):
            entity_type, aggregation_type, field = db_key[:3]
            path = db_key[3:]
            key = tuple(path)
            return key, field, key

        return _aggregate_by_path

    elif filter is not None and filter.get('form_code'):
        def _aggregate_by_entity_by_form_code(db_key):
            filter_key = (db_key[BY_VALUES_ENTITY_ID_INDEX],db_key[BY_VALUES_FORM_CODE_INDEX])
            key = db_key[BY_VALUES_ENTITY_ID_INDEX]
            field = db_key[BY_VALUES_FIELD_INDEX]
            return key, field , filter_key
        return _aggregate_by_entity_by_form_code

    else:
        def _aggregate_by_entity(db_key):
            key = db_key[BY_VALUES_ENTITY_ID_INDEX]
            field = db_key[BY_VALUES_FIELD_INDEX]
            return key, field, key

        return _aggregate_by_entity


def _get_interested_keys_for_location(aggregate_on, dbm, entity_type, location):
    if aggregate_on:
        interested_keys = [tuple(location)]
    else:
        interested_keys = _get_entities_for_location(dbm, entity_type, location)
    return interested_keys

def _get_interested_keys_for_form_code(values, form_code):
    interested_keys = []
    for k,d in values:
        if form_code in k:
            interested_keys.append((k[BY_VALUES_ENTITY_ID_INDEX],k[BY_VALUES_FORM_CODE_INDEX]))
    return interested_keys

def fetch(dbm, entity_type, aggregates=None, aggregate_on=None, starttime=None, endtime=None, filter=None):
    result = {}
    aggregates = {} if aggregates is None else aggregates
    aggregate_on = {} if aggregate_on is None else aggregate_on
    if aggregate_on:
        values = _load_all_fields_by_aggregation_path(dbm, entity_type, aggregate_on)
    else:
        values = _load_all_fields_aggregated(dbm, entity_type, filter)

    interested_keys = None
    if filter:
        location = filter.get("location")
        form_code = filter.get("form_code")
        if location is not None:
            interested_keys = _get_interested_keys_for_location(aggregate_on, dbm, entity_type, location)
        if form_code is not None:
            interested_keys =  _get_interested_keys_for_form_code(values, form_code)

    _parse_key = _get_key_strategy(aggregate_on, filter)



    for key, val in values:
        result_key, field, filter_key = _parse_key(key)
        if filter and filter_key not in interested_keys:
            continue
        interested_aggregate = None
        if field in aggregates:
            interested_aggregate = aggregates.get(field)
            #        * overrides field specific aggregation, returns the aggregation for all fields.
        if "*" in aggregates:
            interested_aggregate = aggregates.get("*")
        if interested_aggregate:
            try:
                result.setdefault(result_key, {})[field] = val[interested_aggregate]
            except KeyError:
                raise AggregationNotSupportedForTypeException(field,interested_aggregate)
    return result


def _load_all_fields_latest_values(dbm, type_path, filter=None):
    view_name = "by_values_latest"
    startkey = [type_path]
    endkey = [type_path, {}]
    if filter is not None and filter.get('form_code') is not None:
        view_group_level = BY_VALUES_FORM_CODE_INDEX + 1
    else:
        view_group_level = BY_VALUES_FIELD_INDEX + 1
    rows = dbm.load_all_rows_in_view(view_name, group_level=view_group_level,
                                     startkey=startkey,
                                     endkey=endkey)
    values = []
    for row in rows:
        values.append((row.key, row.value))
    return values


def _find_in(values, key):
    for k, v in values:
        if k == key:
            return v
    return None


def _load_all_fields_aggregated(dbm, type_path,filter=None):
    view_name = "by_values"
    startkey = [type_path]
    endkey = [type_path, {}]
    if filter is not None and filter.get('form_code') is not None:
        view_group_level = BY_VALUES_FORM_CODE_INDEX + 1
    else:
        view_group_level = BY_VALUES_FIELD_INDEX + 1
    rows = dbm.load_all_rows_in_view(view_name, group_level=view_group_level,
                                     startkey=startkey,
                                     endkey=endkey)
    values = []
    for row in rows:
        values.append((row.key, row.value))

    latest_values = _load_all_fields_latest_values(dbm, type_path, filter)

    for k, v in values:
        v["latest"] = _find_in(latest_values, k)["latest"]
        v['avg'] = v['sum']/v['count']

    for k, v in latest_values:
        v_dict = _find_in(values, k)
        if v_dict is not None:
            v.update(v_dict)

    return latest_values


def _load_all_fields_by_aggregation_path(dbm, entity_type, aggregate_on):
    view_name = "by_aggregation_path"
    aggregation_type = _translate_aggregation_type(aggregate_on)
    rows = dbm.load_all_rows_in_view(view_name, group_level=aggregate_on['level'] + 3,
                                     startkey=[entity_type, aggregation_type],
                                     endkey=[entity_type, aggregation_type, {}])
    values = []
    for row in rows:
        values.append((row.key, row.value))
    return values


def _translate_aggregation_type(aggregate_on):
    AGGREGATE_ON_MAP = {'location': attributes.GEO_PATH}
    aggregate_on_type = aggregate_on['type']
    return AGGREGATE_ON_MAP[aggregate_on_type] if aggregate_on_type in AGGREGATE_ON_MAP else aggregate_on_type


def _get_entities_for_location(dbm, entity_type, location):
    view_name = "by_location"
    rows = dbm.load_all_rows_in_view(view_name, startkey=[entity_type, location],
                                         endkey=[entity_type, location, {}])
    values = []
    for row in rows:
        values.append(row.value)
    return values
