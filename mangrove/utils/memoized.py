# taken from https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize

import collections
import functools
from mangrove.datastore.database import DatabaseManager


class memoized(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
        @memoized
        def testCache(i):
            print "in method " + str(i)
            return i*i;


        testCache(1)
        testCache(2)
        testCache(2)

    '''

    def __init__(self, func):
        #print "Cache time is " + str(ttl)
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        key = tuple([arg.database.name if isinstance(arg, DatabaseManager) else arg for arg in args])
        if key in self.cache:
            return self.cache[key]
        else:
            value = self.func(*args)
            self.cache[key] = value
            return value

    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__

    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)
    def clear(self):
        self.cache = {}


