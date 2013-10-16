

from dates import js_datestring_to_py_datetime, py_datetime_to_js_datestring
from types import is_sequence

try:
    import simplejson as json
except ImportError:
    import json


#
# JSON Helpers
#

class _json_encoder(json.JSONEncoder):
    def default(self, o):
        try:
            return py_datetime_to_js_datestring(o)
        except ValueError:
            # wasn't a date
            pass
        return json.JSONEncoder.default(self, o)


def _decode_hook(s):
    out = {}
    for k in s:
        v = s[k]
        if isinstance(v, basestring):
            try:
                v = js_datestring_to_py_datetime(v)
            except ValueError:
                # wasn't a date
                pass
        elif not isinstance(v, dict) and is_sequence(v):
            # it's a sequence that isn't a dict, so process it
            newv = []
            for i in v:
                try:
                    i = js_datestring_to_py_datetime(i)
                except ValueError:
                    # wasn't a date
                    pass
                newv.append(i)
                v = newv
        out[k] = v
    return out


def decode_json(s):
    return json.loads(s, object_hook=_decode_hook)


def encode_json(o):
    return json.dumps(o, cls=_json_encoder)
