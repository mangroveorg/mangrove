
from glob import iglob
import string
import os

def _find_views():
    views = {}
    for fn in iglob(os.path.join(os.path.dirname(__file__), '*.js')):
        try:
            func, name = string.split(os.path.splitext(os.path.basename(fn))[0], '_', 1)
            with open(fn) as f:
                if name not in views:
                    views[name] = {}
                views[name][func] = f.read()
        except Exception: #TODO Catch the proper exception here, this is a fix to make PyCharm stop complaining. Earlier no exception was being caught here.
            # doesn't match pattern, or file could be read, just skip
            pass
    return views

view_js = _find_views()