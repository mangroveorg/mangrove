# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from _collections import defaultdict
from mangrove.datastore.data import get_latest
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.utils.types import is_empty


class Aggregate(object):
    def __init__(self, field_name,aggregate_name):
        self.field_name = field_name
        self._aggregate_name = aggregate_name

    def get(self,record):
        return record.get(self.aggregate_name)

    @property
    def aggregate_name(self):
        return self._aggregate_name

class Sum(Aggregate):
    def __init__(self, field_name):
        super(Sum,self).__init__(field_name,"sum")

class Min(Aggregate):
    def __init__(self, field_name):
        super(Min,self).__init__(field_name,"min")


class Max(Aggregate):
    def __init__(self, field_name):
        super(Max,self).__init__(field_name,"max")

class Latest(Aggregate):
    def __init__(self, field_name):
        super(Latest,self).__init__(field_name,"latest")

class Month(object):
    def __init__(self, month,year):
        self.month = month
        self.year = year

    @property
    def stats_view(self):
        return "monthly_aggregate_stats"

    @property
    def latest_view(self):
        return "monthly_aggregate_latest"


class TimePeriodViewFinder(object):
    pass


def get_aggregate_view(period):
    pass


def _get_aggregates_for_field(field_name,aggregates,row):
    for aggregate in aggregates:
        if aggregate.field_name == field_name:
            return aggregate.get(row.value)
    return None


def _load_aggregate_view(dbm, form_model, period):
    startkey = [period.year, period.month, form_model.form_code, form_model.entity_type]
    rows = dbm.load_all_rows_in_view(period.stats_view, group=True,
                                     startkey=startkey,
                                     endkey=startkey + [{}])
    return rows


def _get_short_code(row):
    short_code = row.key[-2]
    return short_code


def _get_field_name(row):
    field_name = row.key[-1]
    return field_name


def _get_stats_aggregation(aggregates, dbm, form_model, period):
    rows = _load_aggregate_view(dbm, form_model, period)
    results = defaultdict(dict)
    for row in rows:
        field_name = _get_field_name(row)
        result = _get_aggregates_for_field(field_name, aggregates, row)

        if result is not None:
            results[_get_short_code(row)][field_name] = result
    return results


def _load_latest_view(dbm, form_model, period):
    startkey = [period.year, period.month, form_model.form_code, form_model.entity_type]
    rows = dbm.load_all_rows_in_view(period.latest_view, group=True,
                                     startkey=startkey,
                                     endkey=startkey + [{}])
    return rows


def _get_latest_aggregation(aggregates,dbm,form_model,period):
    rows = _load_latest_view(dbm, form_model, period)
    results = defaultdict(dict)
    for row in rows:
        field_name = _get_field_name(row)
        result = _get_aggregates_for_field(field_name, aggregates, row)
        if result is not None:
            results[_get_short_code(row)][field_name] = result
    return results


def _latest_aggregation_required(aggregates):
    result = filter( lambda x : isinstance(x,Latest), aggregates)
    return not is_empty(result)


def aggregate_for_time_period(dbm, form_code, period,aggregates=None, aggregate_on=None, filter=None,
                                  include_grand_totals = False):
    form_model=get_form_model_by_code(dbm,form_code)
    statsdict = _get_stats_aggregation(aggregates, dbm, form_model, period)

    if _latest_aggregation_required(aggregates):
        latestdict = _get_latest_aggregation(aggregates,dbm,form_model,period)
        return _merge(statsdict,latestdict)

    return statsdict

def _merge(statsdict,latestdict):
    resultdict = defaultdict(dict)
    for key in latestdict:
        resultdict[key] = latestdict[key]
        if key in statsdict:
            resultdict[key].update(statsdict[key])
    return resultdict
