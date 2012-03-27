# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# performing all aggregation in python

from _collections import defaultdict
import time
from mangrove.datastore.data import BY_VALUES_FORM_CODE_INDEX, BY_VALUES_EVENT_TIME_INDEX, EntityAggregration
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.utils.dates import convert_date_string_in_UTC_to_epoch
from mangrove.utils.types import is_string, is_empty

class Sum(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def reduce(self, list_of_values):
        assert isinstance(list_of_values, list)
        try:
            return sum(list_of_values)
        except TypeError:
            return None


class Min(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def reduce(self, list_of_values):
        assert isinstance(list_of_values, list)
        return min(list_of_values)


class Max(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def reduce(self, list_of_values):
        assert isinstance(list_of_values, list)
        return max(list_of_values)


class Latest(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def reduce(self, list_of_values):
        assert isinstance(list_of_values, list)
        return list_of_values[len(list_of_values) - 1] if list_of_values else None


class Count(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def reduce(self, list_of_values):
        assert isinstance(list_of_values, list)
        return len(list_of_values)


class Average(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def reduce(self, list_of_values):
        assert isinstance(list_of_values, list)
        count = len(list_of_values)
        if count > 0:
            return float(sum(list_of_values)) / count

AGGREGATION_DICTIONARY = dict(latest=Latest, sum=Sum, min=Min, max=Max, count=Count, average=Average)

def aggregation_factory(key, field_name):
    return AGGREGATION_DICTIONARY.get(key)(field_name)


def aggregate_by_form_code_python(dbm, form_code, aggregates=None, aggregate_on=None, filter=None,
                                  starttime=None, endtime=None,include_grand_totals = False):
    assert is_string(form_code)
    aggregates = [] if aggregates is None else aggregates

    form = get_form_model_by_code(dbm, form_code)
    values = _map(dbm, form.entity_type, BY_VALUES_FORM_CODE_INDEX, form_code, starttime, endtime, aggregate_on, include_grand_totals)
    return _reduce(aggregates, values)


def _map(dbm, type_path, group_level, form_code=None, start_time=None, end_time=None, aggregate_on=None, include_grand_totals=False):
# currently it assumes one to one mapping between form code and entity type and hence only filter on form code
    view_name = "by_form_code_time"
    epoch_start = convert_date_string_in_UTC_to_epoch(start_time)
    epoch_end = convert_date_string_in_UTC_to_epoch(end_time)
    start_key = [form_code, epoch_start] if epoch_start is not None else [form_code]
    end_key = [form_code, epoch_end] if epoch_end is not None else [form_code, {}]
    rows = dbm.load_all_rows_in_view(view_name, startkey=start_key, endkey=end_key)
    values = []
    for row in rows:
        form_code, timestamp, entity_id, field = row.key
        if include_grand_totals or aggregate_on is None:
            values.append((['GrandTotals', field], row.value))
        if isinstance(aggregate_on, EntityAggregration):
            values.append(([entity_id, field], row.value))

    transformed_values = defaultdict(list)
    for key, value in values:
        transformed_values[tuple(key)].append(value)

    return transformed_values


def _get_aggregate_for_field(aggregates, field_name):
    aggregate_functions = [aggregate for aggregate in aggregates if aggregate.field_name == field_name]
    return aggregate_functions[0] if not is_empty(aggregate_functions) else None


def _reduce(aggregates, values):
    result = defaultdict(dict)
    for (result_key,field_name), value_list in values.items():
        if result_key == 'GrandTotals':
            aggregate_func = Sum('')
        else:
            aggregate_func = _get_aggregate_for_field(aggregates, field_name)
        if aggregate_func:
            aggregate = aggregate_func
            result[result_key][field_name] = aggregate.reduce(value_list)
    return result


def _form_code_filter(row, group_level, form_code):
    return True if form_code is None else row.key[group_level] == form_code


def _start_time_filter(row, start_time):
    if start_time is None:
        return True
    epoch = int(time.mktime(time.strptime(start_time, '%d-%m-%Y %H:%M:%S'))) * 1000
    return row.key[BY_VALUES_EVENT_TIME_INDEX] >= epoch


def _end_time_filter(row, end_time):
    if end_time is None:
        return True
    epoch = convert_date_string_in_UTC_to_epoch(end_time)
    return row.key[BY_VALUES_EVENT_TIME_INDEX] <= epoch


def _should_include_row(row, group_level, form_code, start_time, end_time):
    return _start_time_filter(row, start_time) and\
           _end_time_filter(row, end_time)
