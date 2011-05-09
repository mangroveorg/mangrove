# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from numbers import Number
from datetime import datetime


def is_empty(arg):
    '''
    Generalizes 'empty' checks on Strings, sequences, and dicts.

    Returns 'True' for None, empty strings, strings with just white-space,
    and sequences with len == 0
    '''

    if arg is None:
        return True

    if is_string(arg):
        arg = arg.strip()

    try:
        if len(arg) == 0:
            return True
    except TypeError:
        # wasn't a sequence
        pass

    return False


def is_not_empty(arg):
    '''Convenience inverse of is_empty '''
    return not is_empty(arg)


def is_sequence(arg):
    '''Returns True is passed arg is a list or a tuple'''
    return isinstance(arg, list) or isinstance(arg, tuple)

def is_iterable(arg):
    '''Returns True is passed arg is iterable--e.g. 'in' and 'for x in' work with it'''
    return hasattr(arg, '__iter__')



def is_string(arg):
    '''Test for string in proper way to handle both strings and unicode strings'''
    return isinstance(arg, basestring)


def is_number(arg):
    '''True if arg is any type in Pythons "number tower"

    **Note** This includes Booleans!
    '''
    return isinstance(arg, Number)


def string_as_bool(arg):
    '''True if the argument is any of ("t", "true", "y", "yes", "1", false otherwise'''
    if arg is not None and unicode(arg).lower() in (u'y', u'yes', u't', u'true', u'1'):
        return True
    return False


def primitive_type(arg):
    ''' Returns a string representing the primitive type.

    Options are: 'unknown' 'boolean', 'numeric', 'text', 'datetime'
    '''
    # TODO: Should we have a 'coordinate' or geocode type?
    typ = 'unknown'
    if isinstance(arg, bool):
        typ = 'boolean'
    elif is_number(arg):
        typ = 'numeric'
    elif isinstance(arg, datetime):
        typ = 'datetime'
    elif is_string(arg):
        typ = 'text'
    return typ
