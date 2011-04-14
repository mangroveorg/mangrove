# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os
from glob import iglob
import string

def create_views(dbm):
    '''Creates a standard set of views in the database'''
    global view_js
    database_manager = dbm
    for v in view_js.keys():
        if not exists_view(v, database_manager):
            funcs = view_js[v]
            map = (funcs['map'] if 'map' in funcs else None)
            reduce = (funcs['reduce'] if 'reduce' in funcs else None)
            database_manager.create_view(v, map, reduce)

def exists_view(aggregation, database_manager):
    entity_type_views = database_manager.load('_design/mangrove_views')
    if entity_type_views is not None and entity_type_views['views'].get(aggregation):
        return True
    return False

def find_views():
    views = {}
    for fn in iglob(os.path.join(os.path.dirname(__file__), '*.js')):
        try:
            func, name = string.split(os.path.splitext(os.path.basename(fn))[0],'_',1)
            with open(fn) as f:
                if name not in views:
                    views[name] = {}
                views[name][func]=f.read()
        except:
            # doesn't match pattern, or file could be read, just skip
            pass
    return views

view_js = find_views()
        
