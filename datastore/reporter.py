# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import entity
from mangrove.errors.MangroveException import NumberNotRegisteredException

def check_is_registered(dbm, from_number):
    reporter_list = entity.get_entities_by_type(dbm, "Reporter")
    number_list = []
    for reporter in reporter_list:
        reporter_data = reporter.get_all_data()
        number_list.extend([data["data"]["telephone_number"]["value"]for data in reporter_data])
    if from_number not in number_list:
        raise NumberNotRegisteredException("Sorry, This number is not registered with us")
