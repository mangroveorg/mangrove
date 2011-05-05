"""
    Holds global runtime config options like database, server settings.
    Different from settings.py which holds default startup values.
"""
import settings

_server = settings.SERVER
_db = settings.DATABASE

def set_database(db):
    """
        Allows switching database at runtime.
        """
    global _db
    _db = db

def set_server(url):
    global _server
    _server = url


def reset():
    global _server,_db
    _server = settings.SERVER
    _db = settings.DATABASE
