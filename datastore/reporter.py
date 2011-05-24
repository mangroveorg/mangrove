# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from mangrove.errors.MangroveException import NumberNotRegisteredException
from mangrove.datastore import data

REPORTER_ENTITY_TYPE = ["Reporter"]


def find_reporter(dbm, from_number,entity_type,transport):
    if transport == 'web':
        return None

    if entity_type == 'Reporter':
        return None

    reporters = data.fetch(dbm, entity_type=["Reporter"],
                            aggregates={"telephone_number": data.reduce_functions.LATEST,
                                        "first_name": data.reduce_functions.LATEST}
                          )
    from_reporter_list = [reporters[x] for x in reporters if reporters[x]["telephone_number"] == from_number]
    if not len(from_reporter_list):
        raise NumberNotRegisteredException(from_number)
    return from_reporter_list
