from abc import ABC, abstractmethod
from typing import Any, Dict, List, TypeVar, Type

T = TypeVar("T")

class ISessionManager(ABC):
    @abstractmethod
    def session(self, session_id: str):
        """
        create a unique user session from given session_id

        :param session_id: unique session id (wa_id, mobile_no)
        :return: self
        """
        pass

    @abstractmethod
    def save(self, session_id: str, key: str, data: Any) -> None:
        pass

    @abstractmethod
    def get(self, session_id: str, key: str, t: Type[T] = None) -> Any or T:
        """
         Get data by `key` for given `session_id` from session.

         If t is defined, cast the returned data to type and return it.

        :param session_id: unique session id (wa_id, mobile_no)
        :param key: reference data key
        :param t: data type
        :return: Object
        """
        pass

    @abstractmethod
    def get_global(self, key: str, t: Type[T] = None) -> Any or T:
        pass

    @abstractmethod
    def fetch_all(self, session_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def evict(self, session_id: str, key: str) -> None:
        pass

    @abstractmethod
    def save_all(self, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def evict_all(self, data: List[str]) -> None:
        pass

    @abstractmethod
    def evict_global(self) -> None:
        pass

    @abstractmethod
    def clear(self, session_id: str, retain_keys: List[str] = None) -> None:
        pass

    @abstractmethod
    def evict_prop(self, session_id: str, prop_key: str) -> bool:
        pass

    @abstractmethod
    def get_from_props(self, session_id: str, prop_key: str, t: Type[T] = None) -> Any or T:
        pass

    @abstractmethod
    def key_in_session(self, session_id: str, key: str, check_global: bool = True) -> bool:
        pass

    @abstractmethod
    def get_user_props(self, session_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_global(self, key: str, data: Any) -> None:
        pass

    @abstractmethod
    def save_prop(self, session_id: str, key: str, data: Any) -> None:
        pass
