import re

from src.constants.engine import EngineConstants


class EngineUtil:
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
