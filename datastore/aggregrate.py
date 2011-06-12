# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from _collections import defaultdict
from mangrove.datastore.data import BY_VALUES_FORM_CODE_INDEX
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.utils.types import is_string

class SumAggregrate(object):
    def __init__(self,field_name):
        self.field_name=field_name

    def compute(self,list_of_values):
        assert isinstance(list_of_values,list)
        return sum(list_of_values)

class MinAggregrate(object):
    def __init__(self,field_name):
        self.field_name=field_name

    def compute(self,list_of_values):
        assert isinstance(list_of_values,list)
        return min(list_of_values)

class MaxAggregrate(object):
    def __init__(self,field_name):
        self.field_name=field_name

    def compute(self,list_of_values):
        assert isinstance(list_of_values,list)
        return max(list_of_values)

class LatestAggregrate(object):
    def __init__(self,field_name):
        self.field_name=field_name

    def compute(self,list_of_values):
        assert isinstance(list_of_values,list)
        return list_of_values[0] if list_of_values else None

def aggregate_by_form_code_with_time_filter(dbm, form_code, aggregates=None, aggregate_on=None, filter=None,starttime=None, endtime=None):
    assert is_string(form_code)
    result = {}
    aggregates = [] if aggregates is None else aggregates

    form = get_form_model_by_code(dbm, form_code)
#    aggregate,group_level = _load_all_fields(aggregate_on)
    values = _map(dbm, form.entity_type, BY_VALUES_FORM_CODE_INDEX,form_code)

    values_dict=defaultdict(dict)
    for key,value_list in values.items():
        aggregate_funcs = [aggregate for aggregate in aggregates if aggregate.field_name == key[1]]
        if aggregate_funcs:
            aggregate= aggregate_funcs[0]
            values_dict[key[0]][key[1]]= aggregate.compute(value_list)


#    interested_keys =  _get_interested_keys_for_form_code(values, form_code)

#    _parse_key = _get_key_strategy(aggregate_on, {'form_code':form_code})



#    for key, val in values:
#        result_key, field, filter_key = _parse_key(key)
##        if filter and filter_key not in interested_keys:
#        if filter_key not in interested_keys:
#            continue
#        interested_aggregate = None
#        if field in aggregates:
#            interested_aggregate = aggregates.get(field)
#            #        * overrides field specific aggregation, returns the aggregation for all fields.
#        if "*" in aggregates:
#            interested_aggregate = aggregates.get("*")
#        if interested_aggregate:
#            try:
#                result.setdefault(result_key, {})[field] = val[interested_aggregate]
#            except KeyError:
#                raise AggregationNotSupportedForTypeException(field,interested_aggregate)
    return values_dict


def _map(dbm, type_path,group_level,form_code=None):
# currently it assumes one to one mapping between form code and entity type and hence only filter on form code
    view_name = "by_values"
    rows = dbm.load_all_rows_in_view(view_name, reduce=False)
    values = []
    for row in rows:
        if row.key[group_level] == form_code:
            values.append((row.key[1:group_level], row.value))

#    values = [(row.key[:group_level+1], row.value) for row in rows if row.key[group_level] is form_code]

    transformed_values=defaultdict(list)
    for key,value in values:
        transformed_values[tuple(key)].append(value)

#    latest_values = _load_all_fields_latest_values(dbm, type_path, group_level,filter)

#    for k, v in values:
#        v["latest"] = _find_in(latest_values, k)["latest"]
#        v['average'] = v['sum']/v['count']
#
#    for k, v in latest_values:
#        v_dict = _find_in(values, k)
#        if v_dict is not None:
#            v.update(v_dict)

    return transformed_values
