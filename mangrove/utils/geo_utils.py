


def convert_to_geometry(lat_long_tuple):
    return {'type': 'Point',
            'coordinates': [lat_long_tuple[0], lat_long_tuple[1]]} if lat_long_tuple is not None else None
