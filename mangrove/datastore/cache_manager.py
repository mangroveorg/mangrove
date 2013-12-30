import pylibmc
from mangrove.datastore.settings import CACHE_SERVERS


def get_cache_manager():
    return pylibmc.Client(CACHE_SERVERS, binary=True, behaviors={"tcp_nodelay": True, "ketama": True})

