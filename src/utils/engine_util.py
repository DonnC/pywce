import re
from datetime import datetime

from src.constants.engine import EngineConstants


class EngineUtil:
    @staticmethod
    def has_session_expired(session_dt_str:str=None) -> bool:
        if session_dt_str is None: return True

        passed_datetime = datetime.fromisoformat(session_dt_str)
        return datetime.now() > passed_datetime

    @staticmethod
    def has_interaction_expired(last_interaction_time:str, max_interaction_in_mins:int):
        """
        Checks if the interaction has expired based on the last interaction time and max allowed duration.

        Args:
            last_interaction_time (str): The last interaction time as an ISO 8601 string.
            max_interaction_in_mins (int): The maximum interaction duration in minutes.

        Returns:
            bool: True if the interaction has expired, False otherwise.
        """
        if last_interaction_time is None:
            return False

        last_interaction = datetime.fromisoformat(last_interaction_time)
        current_time = datetime.now()
        elapsed_minutes = abs((current_time - last_interaction).total_seconds() / 60)
        return elapsed_minutes > max_interaction_in_mins

    @staticmethod
    def is_regex_input(value) -> bool:
        return value.startswith(EngineConstants.REGEX_PLACEHOLDER)

    @staticmethod
    def extract_pattern(pattern) -> str:
        return pattern.split(EngineConstants.REGEX_PLACEHOLDER)[-1].strip()

    @staticmethod
    def is_regex_pattern_match(regex_pattern, text) -> bool:
        """
        Checks if a regex pattern matches any part of the given text.

        :param regex_pattern: The regex pattern to match.
        :param text: The text to check against the regex pattern.
        :return: True if the pattern matches any part of the text, False otherwise.
        """
        return re.search(regex_pattern, text) is not None
