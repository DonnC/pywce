import importlib
import inspect
from functools import wraps
from typing import Callable, Literal, Optional

from pywce.src.models import ExternalHandlerResponse, TemplateTypeConstants
from pywce.src.exceptions import HookError
from pywce.src.models import HookArg
from pywce.src.services.ai_service import AiResponse
from pywce.src.utils.engine_logger import pywce_logger

_logger = pywce_logger(__name__)

# Global registries for hooks
_hook_registry = {}
_dotted_path_registry = {}
_function_cache = {}
_global_pre_hooks = []
_global_post_hooks = []

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
    def map_ai_handler_response(recipient:str, ai_response: AiResponse, agent_name:str="🤖") -> ExternalHandlerResponse:
        # TODO: map all supported ai responses
        if ai_response.typ == "button":
            _type = TemplateTypeConstants.BUTTON

        elif ai_response.typ == "list":
            _type = TemplateTypeConstants.LIST

        else:
            _type = TemplateTypeConstants.TEXT

        return ExternalHandlerResponse(
            typ=_type,
            title=ai_response.title,
            message=f"{agent_name}\n{ai_response.message}",
            options=ai_response.options,
            recipient_id=recipient
        )

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
    def register_global_hook(hook_dotted_path: str, hook_type: Literal["pre", "post"]):
        """
        Register a global pre or post hook.
        :param hook_dotted_path: Dotted path to the hook function.
        :param hook_type: Either "pre" or "post".
        """
        if hook_type == "pre":
            _global_pre_hooks.append(hook_dotted_path)
        elif hook_type == "post":
            _global_post_hooks.append(hook_dotted_path)
        else:
            raise HookError("Invalid hook_type. Use 'pre' or 'post'.")

    @staticmethod
    def register_callable_global_hooks(pre: list[Callable], post: list[Callable]):
        for pre_hook in pre:
            dotted_path = f"{pre_hook.__module__}.{pre_hook.__name__}"

            func = HookService.load_function_from_dotted_path(dotted_path)
            HookService.register_hook(name=dotted_path, func=func)
            HookService.register_global_hook(dotted_path, "pre")

        for post_hook in post:
            dotted_path = f"{post_hook.__module__}.{post_hook.__name__}"

            func = HookService.load_function_from_dotted_path(dotted_path)
            HookService.register_hook(name=dotted_path, func=func)
            HookService.register_global_hook(dotted_path, "post")

    @staticmethod
    def load_function_from_dotted_path(dotted_path: str) -> Callable:
        """
        Load a function or attribute from a given dotted path.

        :param dotted_path: The dotted path to the function or attribute.
        :return: A callable function or method.
        """
        try:
            if dotted_path in _function_cache:
                return _function_cache[dotted_path]

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

            _function_cache[dotted_path] = function
            return function

        except (ImportError, AttributeError, ValueError) as e:
            raise ImportError(f"Could not load function from dotted path '{dotted_path}': {e}")

    @staticmethod
    async def _execute_hook(hook_dotted_path: str, hook_arg: HookArg) -> HookArg:
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

            # implement class based hook

            # Function-based hook
            if inspect.iscoroutinefunction(hook_func):
                return await hook_func(hook_arg)

            return hook_func(hook_arg)

        except Exception as e:
            _logger.error("Hook processing failure. Hook: '%s', error: %s", hook_dotted_path, str(e))
            raise HookError(f"Failed to execute hook: {hook_dotted_path}") from e

    @staticmethod
    async def process_hook(hook_dotted_path: str, hook_arg: HookArg) -> HookArg:
        """
        Execute a function from registry or lazy loading it.

        :param hook_dotted_path: The dotted path to the hook function.
        :param hook_arg: The argument to pass to the hook function.
        :return: The result of the hook function.
        """
        return await HookService._execute_hook(hook_dotted_path, hook_arg)

    @staticmethod
    async def process_global_hooks(hook_type: Literal["pre", "post"], hook_arg: HookArg) -> None:
        try:
            hooks = _global_pre_hooks if hook_type == "pre" else _global_post_hooks
            for pre_hook in hooks:
                await HookService._execute_hook(pre_hook, hook_arg)
        except HookError as e:
            _logger.critical("Global `%s` hook processing failure, error: %s", hook_type, e.message)


# decorator
def hook(func: Callable, global_type: Optional[Literal["pre", "post"]] = None) -> Callable:
    """
    Decorator to register a hook function with validation.

    :param func: The hook function to decorate.
    :param global_type: The type of the global hook being registered.
    :return: The wrapped function.
    """

    def decorator(inner_func: Callable) -> Callable:
        @wraps(inner_func)
        def wrapper(arg: HookArg) -> HookArg:
            if not isinstance(arg, HookArg):
                raise HookError(f"Expected HookArg instance, got {type(arg).__name__}")
            return inner_func(arg)

        # Compute the full dotted path for the function
        full_dotted_path = f"{inner_func.__module__}.{inner_func.__name__}"

        # Eagerly register the hook
        if full_dotted_path not in _hook_registry:
            HookService.register_hook(name=full_dotted_path, func=wrapper)

        if global_type:
            HookService.register_global_hook(full_dotted_path, global_type)

        return wrapper

    if func:
        return decorator(func)

    return decorator
