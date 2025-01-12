import importlib
from typing import Callable

from pywce.engine_logger import get_engine_logger
from pywce.src.exceptions import EngineInternalException
from ..models import HookArg

_logger = get_engine_logger(__name__)


class HookService:
    """
    Hook Service:

    Handle hooks from dotted path given.

    Dynamically call hook functions or class methods.
    All hooks should accept a [HookArg] param and return a [HookArg] response.
    """

    @staticmethod
    def load_function_from_dotted_path(dotted_path: str) -> Callable:
        """
        Load a function or attribute from a given dotted path.

        :param dotted_path: The dotted path to the function or attribute.
        :return: A callable function or method.
        """
        try:
            if not dotted_path:
                raise ValueError("Dotted path cannot be empty.")

            # Split the dotted path and resolve step by step
            parts = dotted_path.split('.')
            module_path = '.'.join(parts[:-1])  # Module path (all except the last part)
            function_name = parts[-1]  # Function or attribute name (last part)

            # Import the module
            module = importlib.import_module(module_path)

            # Resolve the function or attribute
            function = getattr(module, function_name, None)

            if not callable(function):
                raise ValueError(f"Resolved object '{function_name}' is not callable.")

            return function

        except (ImportError, AttributeError, ValueError) as e:
            raise ImportError(f"Could not load function from dotted path '{dotted_path}': {e}")

    @staticmethod
    def process_hook(hook_dotted_path: str, hook_arg: HookArg) -> HookArg:
        """
        Execute a function given a dotted path and arguments.

        :param hook_dotted_path: The dotted path to the hook function.
        :param hook_arg: The argument to pass to the hook function.
        :return: The result of the hook function.
        """

        try:
            function = HookService.load_function_from_dotted_path(hook_dotted_path)

            # Call the function with the provided argument
            return function(hook_arg)
        except Exception as e:
            _logger.error("Hook processing failure. Hook: '%s', error: %s", hook_dotted_path, str(e))
            raise EngineInternalException(f"Failed to execute hook: {hook_dotted_path}") from e
