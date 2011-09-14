# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from _collections import defaultdict
from mangrove.form_model.form_model import get_form_model_by_code


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
    def view(self):
        return "monthly_aggregate_stats"
class TimePeriodViewFinder(object):
    pass


def get_aggregate_view(period):
    pass


def _get_aggregates_for_field(field_name,aggregates,row):
    for aggregate in aggregates:
        if aggregate.field_name == field_name:
            return aggregate.get(row.value)
    return None


def aggregate_for_time_period(dbm, form_code, period,aggregates=None, aggregate_on=None, filter=None,
                                  include_grand_totals = False):

    form_model=get_form_model_by_code(dbm,form_code)

    startkey = [period.year, period.month, form_code, form_model.entity_type]
    rows = dbm.load_all_rows_in_view(period.view,group=True,
                                     startkey=startkey,
                                     endkey=startkey+[{}])

    print rows
    results = defaultdict(dict)
    for row in rows:
        #  result {"cli001":{"patient":100}, "cli002" : {} }
        short_code=row.key[-2]
        field_name = row.key[-1]

        result = _get_aggregates_for_field(field_name,aggregates,row)

        if result is not None:
            results[short_code][field_name] = result

    print results
    return results