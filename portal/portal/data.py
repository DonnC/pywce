# simple global data store
_data_store = {}

def put_global(key, data):
    """Store data globally."""
    global _data_store
    _data_store[key] = data

def fetch_global(key=None):
    """Retrieve stored data."""
    return _data_store if key is None else _data_store.get(key)
