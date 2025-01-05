import threading
from typing import Any, Dict, Type, List

from engine_logger import get_engine_logger
from pysession.isession_manager import ISessionManager, T


class DefaultSessionManager(ISessionManager):
    """
        Default session manager

        Uses python dict datatype to implement simple data storage

        Uses a thread-safe approach using threading.Lock() with context for safety
    """
    def __init__(self):
        self.global_session: Dict[str, Any] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.logger = get_engine_logger(__name__)

        self.logger.debug("Initialized default session manager!")

    @property
    def prop_key(self) -> str:
        return "pywce_prop_key"

    def session(self, session_id: str):
        with self.lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = {}
                self.sessions[session_id][self.prop_key] = {}

        return self

    def save(self, session_id: str, key: str, data: Any) -> None:
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id][key] = data

    def get(self, session_id: str, key: str, t: Type[T] = None) -> Any or T:
        with self.lock:
            data = self.sessions.get(session_id).get(key)

            if data is not None and t is not None:
                return t(data)

            return data

    def get_global(self, key: str, t: Type[T] = None) -> Any or T:
        with self.lock:
            data = self.global_session.get(key)

            if data is not None and t is not None:
                return t(data)

            return data

    def fetch_all(self, session_id: str) -> Dict[str, Any] or None:
        with self.lock:
            return self.sessions.get(session_id)

    def evict(self, session_id: str, key: str) -> None:
        with self.lock:
            self.sessions.get(session_id).pop(key)

    def save_all(self, session_id:str, data: Dict[str, Any]) -> None:
        for k, v in data.items():
            self.save(session_id, k, v)

    def evict_all(self, session_id: str, keys: List[str]) -> None:
        for k in keys:
            self.evict(session_id, k)

    def evict_global(self) -> None:
        with self.lock:
            self.global_session = {}

    def clear(self, session_id: str, retain_keys: List[str] = None) -> None:
        if retain_keys is None or retain_keys == []:
            self.sessions[session_id] = {}

        for retain_key in retain_keys:
            data = self.fetch_all(session_id)
            for k, v in data.items():
                if k == retain_key:
                    continue
                self.evict(session_id, k)

    def key_in_session(self, session_id: str, key: str, check_global: bool = True) -> bool:
        with self.lock:
            if check_global:
                return self.global_session.get(key) is not None

            return self.sessions.get(session_id).get(key) is not None

    def get_user_props(self, session_id: str) -> Dict[str, Any]:
        return self.get(session_id, self.prop_key)

    def evict_prop(self, session_id: str, prop_key: str) -> bool:
        current_props = self.get_user_props(session_id)

        if prop_key not in current_props:
            return False

        current_props.pop(prop_key)

        self.save(session_id, self.prop_key, current_props)

        return True

    def get_from_props(self, session_id: str, prop_key: str, t: Type[T] = None) -> Any or T:
        props = self.get_user_props(session_id)

        if prop_key not in props or props.get(prop_key) is None:
            return None

        prop = props.get(prop_key)

        if t is None:
            return prop

        return t(prop)

    def save_global(self, key: str, data: Any) -> None:
        with self.lock:
            self.global_session[key] = data

    def save_prop(self, session_id: str, prop_key: str, data: Any) -> None:
        current_props = self.get_user_props(session_id)
        current_props[prop_key] = data
        self.save(session_id, self.prop_key, current_props)
