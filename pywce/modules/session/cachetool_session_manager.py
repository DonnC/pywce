import threading
from typing import Any, Dict, Type, List, Union

from pywce.modules.session import ISessionManager
from pywce.src.utils import pywce_logger
from . import T
from ...src.exceptions import EngineException

try:
    from cachetools import TTLCache
except ImportError:
    TTLCache = None


class CachetoolSessionManager(ISessionManager):
    """
    Default session manager using cachetools TTLCache.

    Handles user-specific session data and a global cache with time-to-live (TTL).
    """

    def __init__(self, user_ttl: int = 10 * 60, global_ttl: int = 15 * 60, maxsize: int = 1000):
        """
        Initialize the session manager.

        :param user_ttl: TTL for user session caches (in seconds).
        :param global_ttl: TTL for the global cache (in seconds).
        :param maxsize: Maximum size of the caches.
        """
        self._verify_dependencies()

        self.user_ttl = user_ttl
        self.global_ttl = global_ttl
        self.lock = threading.Lock()
        self.logger = pywce_logger(__name__)

        # Initialize global and per-user session caches
        self.global_cache = TTLCache(maxsize=maxsize, ttl=self.global_ttl)
        self.user_caches: Dict[str, TTLCache] = {}

    def _verify_dependencies(self):
        if TTLCache is None:
            raise EngineException("Cache requires additional dependencies. Install using `pip install pywce[cache]`.")

    @property
    def prop_key(self) -> str:
        return "pywce_prop_key"

    def _get_user_cache(self, session_id: str) -> TTLCache:
        """
        Retrieve or create a user-specific cache.

        :param session_id: The user session ID.
        :return: The TTLCache for the user.
        """
        with self.lock:
            if session_id not in self.user_caches:
                self.user_caches[session_id] = TTLCache(maxsize=1000, ttl=self.user_ttl)
            return self.user_caches[session_id]

    def session(self, session_id: str) -> ISessionManager:
        self._get_user_cache(session_id)
        return self

    def save_all(self, session_id: str, data: Dict[str, Any]) -> None:
        for k, v in data.items():
            self.save(session_id, k, v)

    def evict_all(self, session_id: str, keys: List[str]) -> None:
        for k in keys:
            self.evict(session_id, k)

    def save(self, session_id: str, key: str, data: Any) -> None:
        cache = self._get_user_cache(session_id)
        with self.lock:
            cache[key] = data

    def get(self, session_id: str, key: str, t: Type[T] = None) -> Union[Any, T]:
        cache = self._get_user_cache(session_id)
        with self.lock:
            data = cache.get(key)

            if data is not None and t is not None:
                return t(data)

            return data

    def save_global(self, key: str, data: Any) -> None:
        with self.lock:
            self.global_cache[key] = data

    def get_global(self, key: str, t: Type[T] = None) -> Union[Any, T]:
        with self.lock:
            data = self.global_cache.get(key)

            if data is not None and t is not None:
                return t(data)

            return data

    def fetch_all(self, session_id: str, is_global: bool = False) -> Union[Dict[str, Any], None]:
        with self.lock:
            if is_global:
                return dict(self.global_cache.items())

            cache = self._get_user_cache(session_id)
            return dict(cache.items())

    def evict(self, session_id: str, key: str) -> None:
        cache = self._get_user_cache(session_id)
        with self.lock:
            if key in cache:
                del cache[key]

    def evict_global(self, key: str) -> None:
        with self.lock:
            if key in self.global_cache:
                del self.global_cache[key]

    def clear(self, session_id: str, retain_keys: List[str] = None) -> None:
        cache = self._get_user_cache(session_id)
        with self.lock:
            if not retain_keys:
                cache.clear()
                return

            keys_to_remove = [key for key in cache.keys() if key not in retain_keys]
            for key in keys_to_remove:
                del cache[key]

    def clear_global(self) -> None:
        with self.lock:
            self.global_cache.clear()

    def key_in_session(self, session_id: str, key: str, check_global: bool = True) -> bool:
        with self.lock:
            if check_global and key in self.global_cache:
                return True

            cache = self._get_user_cache(session_id)
            return key in cache

    def get_user_props(self, session_id: str) -> Dict[str, Any]:
        return self.get(session_id, self.prop_key, t=dict) or {}

    def save_prop(self, session_id: str, prop_key: str, data: Any) -> None:
        current_props = self.get_user_props(session_id)
        current_props[prop_key] = data
        self.save(session_id, self.prop_key, current_props)

    def evict_prop(self, session_id: str, prop_key: str) -> bool:
        current_props = self.get_user_props(session_id)

        if prop_key not in current_props:
            return False

        del current_props[prop_key]
        self.save(session_id, self.prop_key, current_props)
        return True

    def get_from_props(self, session_id: str, prop_key: str, t: Type[T] = None) -> Union[Any, T]:
        props = self.get_user_props(session_id)
        if prop_key not in props:
            return None

        prop = props[prop_key]
        return t(prop) if t else prop
