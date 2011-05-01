# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import entity
from mangrove.errors.MangroveException import NumberNotRegisteredException
from mangrove.datastore import data

def check_is_registered(dbm, from_number):
    reporter_list = entity.get_entities_by_type(dbm, "Reporter")
    number_list = []
    for reporter in reporter_list:
        reporter_data = reporter.get_all_data()
        number_list.extend([data["data"]["telephone_number"]["value"]for data in reporter_data])
    if from_number not in number_list:
        raise NumberNotRegisteredException(("Sorry, This number %s is not registered with us") % (from_number,) )

def get_from_reporter(dbm,from_number):
    reporters = data.fetch(dbm, entity_type=["Reporter"],
                            aggregates={"telephone_number": data.reduce_functions.LATEST,"first_name":data.reduce_functions.LATEST}
                          )
    from_reporter_list= [reporters[x] for x in reporters if reporters[x]["telephone_number"]==from_number]
    if len(from_reporter_list) != 1:
        raise NumberNotRegisteredException("Sorry, This number is not registered with us")
    return from_reporter_list[0]

