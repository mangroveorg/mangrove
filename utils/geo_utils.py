# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

def convert_to_geometry(lat_long_tuple):
    return {'type':'Point','coordinates':[lat_long_tuple[0],lat_long_tuple[1]]} if lat_long_tuple is not None else None