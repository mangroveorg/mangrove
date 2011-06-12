# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore.data import EntityAggregration

from mangrove.errors.MangroveException import NumberNotRegisteredException
from mangrove.datastore import data
from mangrove.form_model.form_model import MOBILE_NUMBER_FIELD, NAME_FIELD

REPORTER_ENTITY_TYPE = ["Reporter"]


def find_reporter(dbm, from_number):
    reporters = data.aggregate_by_entity(dbm, entity_type=["Reporter"],
                            aggregates={MOBILE_NUMBER_FIELD: data.reduce_functions.LATEST,
                                        NAME_FIELD: data.reduce_functions.LATEST},aggregate_on=EntityAggregration()
                          )
    from_reporter_list = [reporters[x] for x in reporters if reporters[x].get(MOBILE_NUMBER_FIELD) == from_number]
    if not len(from_reporter_list):
        raise NumberNotRegisteredException(from_number)
    return from_reporter_list
