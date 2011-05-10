# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import urllib
import json
from mangrove.utils.types import is_string, is_number

GEOREGISTRY_API_BASE_URL = 'http://ni-api.georegistry.org/api/1.0'
GEOREGISTRY_API_DEFAULT_LIMIT = 50
GEOREGISTRY_NUM_HTTP_ATTEMPS = 5


def get_locations_tree(country_code, limit=GEOREGISTRY_API_DEFAULT_LIMIT):
    assert is_string(country_code)
    assert is_number(int(limit))
    return _query('/features/locations', country_code=country_code, limit=limit)


def get_feature_by_id(id):
    assert is_string(id)
    return _query('/feature/%s.json' % id)['features'][0]


def _query(url, **params):
    params = urllib.urlencode(params)
    ret_val = False
    for t in range(0, GEOREGISTRY_NUM_HTTP_ATTEMPS):
        try:
            query = GEOREGISTRY_API_BASE_URL + url + '?%s' % params
            data = urllib.urlopen(query)
            print '[%s] ...' % (t + 1)
            if data.getcode() == 200:
                ret_val = json.loads(data.read())
                break
        except IOError as e:
            print e.message
            print 'Query was: %s' % query
    return ret_val
