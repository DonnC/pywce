import logging
import re
from datetime import datetime
from typing import Any, Dict

from jinja2 import Template

from pywce.src.constants import EngineConstants
from pywce.src.exceptions import TemplateRenderException
from pywce.src.templates import EngineRoute

_logger = logging.getLogger(__name__)


class EngineUtil:
    @staticmethod
    def extract_special_vars(value: str, pattern: str) -> list:
        """
        Extract special variables based on a given regex pattern.
        """
        return re.findall(pattern, value)

    @staticmethod
    def render_template(template: Any, context: Dict) -> Any:
        """
        Render the templates using Jinja2 after special variables are replaced.
        """
        try:
            if context is None: return template

            def render_with_jinja(value):
                if isinstance(value, str):
                    return Template(value).render(context)
                return value

            if isinstance(template, dict):
                return {key: EngineUtil.render_template(value, context) for key, value in template.items()}
            elif isinstance(template, list):
                return [EngineUtil.render_template(item, context) for item in template]
            else:
                return render_with_jinja(template)

        except Exception as e:
            _logger.error("Render templates failure: {}".format(str(e)))
            raise TemplateRenderException(message="Template failed to render")

    @staticmethod
    def has_session_expired(session_dt_str: str = None) -> bool:
        if session_dt_str is None: return True

        passed_datetime = datetime.fromisoformat(session_dt_str)
        return datetime.now() > passed_datetime

    @staticmethod
    def has_interaction_expired(last_interaction_time: str, max_interaction_in_mins: int):
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
        if EngineUtil.is_regex_input(pattern):
            return pattern.split(EngineConstants.REGEX_PLACEHOLDER)[-1].strip()
        return pattern

    @staticmethod
    def has_triggered(trigger: EngineRoute, upstream_user_input) -> bool:
        """
        Checks if a regex pattern matches any part of the given text.

        :param trigger: The regex pattern to match.

        :param upstream_user_input: The text to check against the regex pattern.
        :return: True if the pattern matches any part of the text, False otherwise.
        """
        if trigger.is_regex:
            return re.search(EngineUtil.extract_pattern(trigger.user_input), str(upstream_user_input)) is not None

        return str(upstream_user_input) == str(trigger.user_input)
