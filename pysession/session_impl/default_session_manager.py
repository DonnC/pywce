import threading
from typing import Any, Dict, Type, List

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

    def session(self, session_id: str):
        with self.lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = {}

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
        pass

    def fetch_all(self, session_id: str) -> Dict[str, Any]:
        pass

    def evict(self, session_id: str, key: str) -> None:
        pass

    def save_all(self, data: Dict[str, Any]) -> None:
        pass

    def evict_all(self, data: List[str]) -> None:
        pass

    def evict_global(self) -> None:
        pass

    def clear(self, session_id: str, retain_keys: List[str] = None) -> None:
        if retain_keys is None:
            self.sessions[session_id] = {}

        # TODO: clear all info but only retain

    def evict_prop(self, session_id: str, prop_key: str) -> bool:
        pass

    def get_from_props(self, session_id: str, prop_key: str, t: Type[T] = None) -> Any or T:
        pass

    def key_in_session(self, session_id: str, key: str, check_global: bool = True) -> bool:
        pass

    def get_user_props(self, session_id: str) -> Dict[str, Any]:
        pass

    def save_global(self, key: str, data: Any) -> None:
        pass

    def save_prop(self, session_id: str, key: str, data: Any) -> None:
        pass
