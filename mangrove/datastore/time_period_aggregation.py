
from _collections import defaultdict
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.utils.types import is_empty

"""
    Example usage of predefined aggregate:

    1. Monthly Aggregate on all data records for a field per entity for the form code.

    values = aggregate_for_time_period(
        self.manager,
        form_code='CL1',
        aggregates=[Sum("patients"), Min('meds'), Max('beds'),Latest("director")],
        period=Month(2, 2010)
        )

    Returns one row per entity, with the aggregated values for each
    field.
    {"<entity_id>": {"patients": 10, 'meds': 20, 'beds': 300 , 'director': "Dr. A"}}

    2. Weekly Aggregate on all data records for a field per entity for the form code.

    values = aggregate_for_time_period(
        self.manager,
        form_code='CL1',
        aggregates=[Sum("patients"), Min('meds'), Max('beds'),Latest("director")],
        period=Week(52, 2009)
        )

    52 is the weeknumber and 2009 is the year.
    Returns one row per entity, with the aggregated values for each field.
    {"<entity_id>": {"patients": 10, 'meds': 20, 'beds': 300 , 'director': "Dr. A"}}

    2. Yearly Aggregate on all data records for a field per entity for the form code.

    values = aggregate_for_time_period(
        self.manager,
        form_code='CL1',
        aggregates=[Sum("patients"), Min('meds'), Max('beds'),Latest("director")],
        period=Year(2010)
        )

    2010 is the year.
    Returns one row per entity, with the aggregated values for each field.
    {"<entity_id>": {"patients": 10, 'meds': 20, 'beds': 300 , 'director': "Dr. A"}}

    2. Aggregate on a location level = 2

    #TODO
    Returns {("India", "MH"): {"patients": 2}}

    3. All entities, selected fields, filtered by location,

    #TODO

    This returns you one row per entity for all entities of type
    entity_type in Pune with the aggregations applied per field.

    4. Aggregate on a location level = 2, but filter by location,

    #TODO

    5. Aggregate on any hierarchy,

    #TODO

    6. Fetch aggregation for all the fields for all entities of a
    given type, use '*' instead of field name,

    #TODO
"""

def aggregate_for_time_period(dbm, form_code, period, aggregates=None, aggregate_on=None, filter=None,
                              include_grand_totals=False):
    form_model = get_form_model_by_code(dbm, form_code)
    statsdict = _get_stats_aggregation(aggregates, dbm, form_model, period)

    if include_grand_totals is True:
        _calculate_grand_total(statsdict)

    if _latest_aggregation_required(aggregates):
        latestdict = _get_latest_aggregation(aggregates, dbm, form_model, period)
        return _merge(statsdict, latestdict)

    return statsdict


class Aggregate(object):
    def __init__(self, field_name, aggregate_name):
        self.field_name = field_name
        self._aggregate_name = aggregate_name

    def get(self, record):
        return record.get(self.aggregate_name)

    @property
    def aggregate_name(self):
        return self._aggregate_name


class Sum(Aggregate):
    def __init__(self, field_name):
        super(Sum, self).__init__(field_name, "sum")


class Min(Aggregate):
    def __init__(self, field_name):
        super(Min, self).__init__(field_name, "min")


class Max(Aggregate):
    def __init__(self, field_name):
        super(Max, self).__init__(field_name, "max")


class Latest(Aggregate):
    def __init__(self, field_name):
        super(Latest, self).__init__(field_name, "latest")


class Month(object):
    def __init__(self, month, year):
        self.month = month
        self.year = year

    @property
    def stats_view(self):
        return "monthly_aggregate_stats"

    @property
    def period(self):
        return self.month

    @property
    def latest_view(self):
        return "monthly_aggregate_latest"

    @property
    def startkey_start(self):
        return [self.year,self.month]


class Year(object):
    def __init__(self, year):
        self.year = year

    @property
    def stats_view(self):
        return "yearly_aggregate_stats"

    @property
    def period(self):
        return self.year

    @property
    def latest_view(self):
        return "yearly_aggregate_latest"

    @property
    def startkey_start(self):
        return [self.year]


class Week(object):
    def __init__(self, week, year):
        self.week = week
        self.year = year

    @property
    def period(self):
        return self.week

    @property
    def stats_view(self):
        return "weekly_aggregate_stats"

    @property
    def latest_view(self):
        return "weekly_aggregate_latest"

    @property
    def startkey_start(self):
        return [self.year,self.week]

class Day(object):
    def __init__(self, day, month,year):
        self.day= day
        self.month= month
        self.year = year

    @property
    def period(self):
        return self.day

    @property
    def stats_view(self):
        return "daily_aggregate_stats"

    @property
    def latest_view(self):
        return "daily_aggregate_latest"

    @property
    def startkey_start(self):
        return [self.year,self.month,self.day]


def _get_aggregates_for_field(field_name, aggregates, row):
    for aggregate in aggregates:
        if aggregate.field_name == field_name:
            return aggregate.get(row.value)
    return None


def _load_aggregate_view(dbm, form_model, period):
    startkey = period.startkey_start + [form_model.form_code, form_model.entity_type]
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
    startkey = period.startkey_start+[form_model.form_code, form_model.entity_type]
    rows = dbm.load_all_rows_in_view(period.latest_view, group=True,
                                     startkey=startkey,
                                     endkey=startkey + [{}])
    return rows


def _get_latest_aggregation(aggregates, dbm, form_model, period):
    rows = _load_latest_view(dbm, form_model, period)
    results = defaultdict(dict)
    for row in rows:
        field_name = _get_field_name(row)
        result = _get_aggregates_for_field(field_name, aggregates, row)
        if result is not None:
            results[_get_short_code(row)][field_name] = result
    return results


def _latest_aggregation_required(aggregates):
    result = filter(lambda x: isinstance(x, Latest), aggregates)
    return not is_empty(result)


GRAND_TOTALS = "GrandTotals"

def _calculate_grand_total(statsdict):
    intermediate_dict=defaultdict(int)
    for key,value in statsdict.items():
        for key,value in value.items():
            intermediate_dict[key]+=value

    statsdict[GRAND_TOTALS]=intermediate_dict



def _merge_grand_total(resultdict, statsdict):
    grand_total = statsdict.get(GRAND_TOTALS)
    if grand_total is not None:
        resultdict[GRAND_TOTALS] = grand_total


def _merge(statsdict, latestdict):
    resultdict = defaultdict(dict)
    for key in latestdict:
        resultdict[key] = latestdict[key]
        if key in statsdict:
            resultdict[key].update(statsdict[key])
    _merge_grand_total(resultdict, statsdict)
    return resultdict
