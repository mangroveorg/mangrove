# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from documents import attributes
from mangrove.errors.MangroveException import AggregationNotSupportedForTypeException
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.utils.types import is_string

BY_VALUES_ENTITY_ID_INDEX = 1
BY_VALUES_FIELD_INDEX = BY_VALUES_ENTITY_ID_INDEX + 1
BY_VALUES_FORM_CODE_INDEX = BY_VALUES_FIELD_INDEX + 1
BY_VALUES_EVENT_TIME_INDEX = BY_VALUES_FORM_CODE_INDEX + 1

FORM_CODE_GROUP_LEVEL = BY_VALUES_FORM_CODE_INDEX + 1
ENTITY_GROUP_LEVEL = BY_VALUES_FIELD_INDEX + 1

class reduce_functions(object):
    """""Constants for referencing reduce functions. """""
    SUM = "sum"
    LATEST = "latest"
    COUNT = "count"  # Returns number of records containing the field
    AVG = 'average'
    MIN = 'min'
    MAX = 'max'

    SUPPORTED_FUNCTIONS = [SUM, LATEST, COUNT, AVG, MIN, MAX]


class by(object):
    """""Constants for defining the aggregation type """""
    LOCATION = "location"
    ENTITY = "entity"
    AGGREGRATION_TREE = "aggregation_tree"


class LocationAggregration(object):
    def __init__(self, level=0):
        self.level = level


class TypeAggregration(object):
    def __init__(self, type, level=0):
        self.type = type
        self.level = level


class EntityAggregration(object):
    pass


class LocationFilter(object):
    def __init__(self, location):
        self.location = location


def _load_entity_attributes(dbm, entity_type):
    view_name = "get_entity_attributes"
    startkey = [entity_type]
    endkey = [entity_type, {}]
    rows = dbm.load_all_rows_in_view(view_name, startkey=startkey,
                                     endkey=endkey)
    values = {}
    for row in rows:
        values[row.key[1]] = row.value
    return values


def get_latest(dbm, entity_type):
    return _load_entity_attributes(dbm, entity_type)


def aggregate(dbm, entity_type, aggregates=None, aggregate_on=None,
              filter=None, starttime=None, endtime=None):
    """
    Example usage of aggregate:

    1. Aggregate on all data records for a field per entity.

    values = data.aggregate(
        self.manager,
        entity_type=ENTITY_TYPE,
        aggregates={
            "director": data.reduce_functions.LATEST,
            "beds": data.reduce_functions.LATEST,
            "patients": data.reduce_functions.SUM
            },
        aggregate_on=EntityAggregration()
        )

    Returns one row per entity, with the aggregated values for each
    field.
    {"<entity_id>": {"director": "Dr. A", "beds": 500, "patients": 30}}

    2. Aggregate on a location level = 2

    values = data.aggregate(
        self.manager,
        entity_type=ENTITY_TYPE,
        aggregates={
            "patients": data.reduce_functions.SUM
            },
        aggregate_on=LocationAggregration(level=2)
        )

    Returns {("India", "MH"): {"patients": 2}}

    3. All entities, selected fields, filtered by location,

    values = data.aggregate(
        self.manager,
        entity_type=ENTITY_TYPE,
        aggregate_on=EntityAggregration(),
        aggregates={
            "director": data.reduce_functions.LATEST,
            "beds": data.reduce_functions.LATEST,
            "patients": data.reduce_functions.SUM
            },
        filter=LocationFilter(['India', 'MH', 'Pune'])
        )

    This returns you one row per entity for all entities of type
    entity_type in Pune with the aggregations applied per field.

    4. Aggregate on a location level = 2, but filter by location,

    values = data.aggregate(
        self.manager,
        entity_type=ENTITY_TYPE,
        aggregates={
            "patients": data.reduce_functions.SUM
            },
        aggregate_on=LocationAggregration(level=2),
        filter=LocationFilter(['India', 'MH'])
        )

    5. Aggregate on any hierarchy,

    values = data.aggregate(
        self.manager,
        entity_type=ENTITY_TYPE,
        aggregates={
            "patients": data.reduce_functions.SUM
            },
        aggregate_on=TypeAggregration(type='governance', level=3)
        )

    6. Fetch aggregation for all the fields for all entities of a
    given type, use '*' instead of field name,

    values = data.aggregate(
        self.manager,
        entity_type=ENTITY_TYPE,
        aggregates={
            "*": data.reduce_functions.LATEST
            },
        aggregate_on=EntityAggregration()
        )
    """
    result = {}
    aggregates = {} if aggregates is None else aggregates

    aggregate, group_level = _get_aggregate_strategy(aggregate_on)
    values = aggregate(dbm, entity_type, group_level, aggregate_on)
    interested_keys = None

    if isinstance(filter, LocationFilter):
        interested_keys = _get_interested_keys_for_location(aggregate_on, dbm, entity_type, filter.location)

    _parse_key = _get_key_strategy(aggregate_on, dict())

    for key, val in values:
        result_key, field, filter_key = _parse_key(key)
        #        if filter and filter_key not in interested_keys:
        if interested_keys is not None and filter_key not in interested_keys:
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
                raise AggregationNotSupportedForTypeException(field, interested_aggregate)
    return result


def aggregate_for_form(dbm, form_code, aggregates=None, aggregate_on=None, filter=None, starttime=None, endtime=None):
    assert is_string(form_code)
    result = {}
    aggregates = {} if aggregates is None else aggregates

    form = get_form_model_by_code(dbm, form_code)
    aggregate, group_level = _get_aggregate_strategy(aggregate_on, for_form_code=True)
    values = aggregate(dbm, form.entity_type, group_level, aggregate_on)

    interested_keys = _get_interested_keys_for_form_code(values, form_code)

    _parse_key = _get_key_strategy(aggregate_on, {'form_code': form_code})

    for key, val in values:
        result_key, field, filter_key = _parse_key(key)
        #        if filter and filter_key not in interested_keys:
        if filter_key not in interested_keys:
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
                raise AggregationNotSupportedForTypeException(field, interested_aggregate)
    return result


def _get_interested_keys_for_form_code(values, form_code):
    interested_keys = []
    for k, d in values:
        if form_code in k:
            interested_keys.append((k[BY_VALUES_ENTITY_ID_INDEX], k[BY_VALUES_FORM_CODE_INDEX]))
    return interested_keys


def _get_interested_keys_for_location(aggregate_on, dbm, entity_type, location):
    if isinstance(aggregate_on, LocationAggregration) or isinstance(aggregate_on, TypeAggregration):
        interested_keys = [tuple(location)]
    else:
        interested_keys = _get_entities_for_location(dbm, entity_type, location)
    return interested_keys


def _get_key_strategy(aggregate_on, filter):
    if isinstance(aggregate_on, LocationAggregration) or isinstance(aggregate_on, TypeAggregration):
        def _aggregate_by_path(db_key):
            entity_type, aggregation_type, field = db_key[:3]
            path = db_key[3:]
            key = tuple(path)
            return key, field, key

        return _aggregate_by_path

    elif filter is not None and filter.get('form_code'):
        def _aggregate_by_entity_by_form_code(db_key):
            filter_key = (db_key[BY_VALUES_ENTITY_ID_INDEX], db_key[BY_VALUES_FORM_CODE_INDEX])
            key = db_key[BY_VALUES_ENTITY_ID_INDEX]
            field = db_key[BY_VALUES_FIELD_INDEX]
            return key, field, filter_key

        return _aggregate_by_entity_by_form_code

    else:
        def _aggregate_by_entity(db_key):
            key = db_key[BY_VALUES_ENTITY_ID_INDEX]
            field = db_key[BY_VALUES_FIELD_INDEX]
            return key, field, key

        return _aggregate_by_entity


def _get_aggregate_strategy(aggregate_on, for_form_code=False):
    if isinstance(aggregate_on, LocationAggregration) or isinstance(aggregate_on, TypeAggregration):
        return _load_all_fields_by_aggregation_path, aggregate_on.level
    else:
        group_level = FORM_CODE_GROUP_LEVEL if for_form_code is True else ENTITY_GROUP_LEVEL
        return _load_all_fields_aggregated, group_level


def _load_all_fields_latest_values(dbm, type_path, group_level, filter=None):
    view_name = "by_values_latest"
    startkey = [type_path]
    endkey = [type_path, {}]
    #    if filter is not None and filter.get('form_code') is not None:
    view_group_level = BY_VALUES_FORM_CODE_INDEX + 1
    #    else:
    #        view_group_level = BY_VALUES_FIELD_INDEX + 1
    rows = dbm.load_all_rows_in_view(view_name, group_level=group_level,
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


def _load_all_fields_aggregated(dbm, type_path, group_level, filter=None):
    view_name = "by_values"
    startkey = [type_path]
    endkey = [type_path, {}]
    #    if filter is not None and filter.get('form_code') is not None:
    #        view_group_level = BY_VALUES_FORM_CODE_INDEX + 1
    #    else:
    #        view_group_level = BY_VALUES_FIELD_INDEX + 1
    rows = dbm.load_all_rows_in_view(view_name, group_level=group_level,
                                     startkey=startkey,
                                     endkey=endkey)
    values = []
    for row in rows:
        values.append((row.key, row.value))

    latest_values = _load_all_fields_latest_values(dbm, type_path, group_level, filter)

    for k, v in values:
        v["latest"] = _find_in(latest_values, k)["latest"]
        v['average'] = v['sum'] / v['count']

    for k, v in latest_values:
        v_dict = _find_in(values, k)
        if v_dict is not None:
            v.update(v_dict)

    return latest_values


def _load_all_fields_by_aggregation_path(dbm, entity_type, aggregate_on_level, aggregate_on):
    view_name = "by_aggregation_path"
    aggregation_type = _translate_aggregation_type(aggregate_on)
    rows = dbm.load_all_rows_in_view(view_name, group_level=aggregate_on_level + 3,
                                     startkey=[entity_type, aggregation_type],
                                     endkey=[entity_type, aggregation_type, {}])
    values = []
    for row in rows:
        values.append((row.key, row.value))
    return values


def _translate_aggregation_type(aggregate_on):
    AGGREGATE_ON_MAP = {'location': attributes.GEO_PATH}
    #    aggregate_on_type = aggregate_on['type']
    return attributes.GEO_PATH if isinstance(aggregate_on, LocationAggregration) else aggregate_on.type


def _get_entities_for_location(dbm, entity_type, location):
    view_name = "by_location"
    rows = dbm.load_all_rows_in_view(view_name, startkey=[entity_type, location],
                                     endkey=[entity_type, location, {}])
    values = []
    for row in rows:
        values.append(row.value)
    return values
