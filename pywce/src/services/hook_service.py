import importlib
from functools import wraps
from typing import Callable

from pywce.src.exceptions import HookError
from pywce.src.models import HookArg
from pywce.src.utils.engine_logger import pywce_logger

_logger = pywce_logger(__name__)

# Global registries for hooks
_hook_registry = {}
_dotted_path_registry = {}

class HookService:
    """
    Hook Service:

    Handle hooks from dotted path given.

    Dynamically call hook functions or class methods.
    All hooks should accept a [HookArg] param and return a [HookArg] response.
    """

    @staticmethod
    def registry():
        return _hook_registry

    @staticmethod
    def path_registry():
        return _dotted_path_registry

    @staticmethod
    def register_hook(name: str, func: Callable = None, dotted_path: str = None):
        """
        Register a hook function or its dotted path for lazy loading.

        :param name: The name of the hook function.
        :param func: The actual function to register.
        :param dotted_path: The dotted path to a function for lazy loading.
        """
        if func:
            _hook_registry[name] = func
        elif dotted_path:
            _dotted_path_registry[name] = dotted_path

        _logger.debug("Registered %s hook: %s", "func" if func else "path", name)

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
        Execute a function from registry or lazy loading it.

        :param hook_dotted_path: The dotted path to the hook function.
        :param hook_arg: The argument to pass to the hook function.
        :return: The result of the hook function.
        """
        try:
            if hook_dotted_path in _hook_registry:
                # Retrieve the eagerly registered hook
                hook_func = _hook_registry[hook_dotted_path]

            elif hook_dotted_path in _dotted_path_registry:
                # Lazily resolve the hook
                dotted_path = _dotted_path_registry[hook_dotted_path]
                hook_func = HookService.load_function_from_dotted_path(dotted_path)
                _hook_registry[hook_dotted_path] = hook_func

            else:
                hook_func = HookService.load_function_from_dotted_path(hook_dotted_path)
                HookService.register_hook(name=hook_dotted_path, dotted_path=hook_dotted_path)

            return hook_func(hook_arg)

        except Exception as e:
            _logger.error("Hook processing failure. Hook: '%s', error: %s", hook_dotted_path, str(e))
            raise HookError(f"Failed to execute hook: {hook_dotted_path}") from e


def hook(func: Callable) -> Callable:
    """
    Decorator to register a hook function with validation.

    :param func: The hook function to decorate.
    :return: The wrapped function.
    """

    @wraps(func)
    def wrapper(arg: HookArg) -> HookArg:
        if not isinstance(arg, HookArg):
            raise HookError(f"Expected HookArg instance, got {type(arg).__name__}")

        _logger.debug("Invoking hook: %s", func.__name__)
        return func(arg)

    # Compute the full dotted path for the function
    full_dotted_path = f"{func.__module__}.{func.__name__}"

    # Eagerly register the hook
    if full_dotted_path not in _hook_registry:
        HookService.register_hook(name=full_dotted_path, func=func)

    return wrapper
