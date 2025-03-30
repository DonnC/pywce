import inspect
from typing import Optional, Callable

from pywce.src.constants import EngineConstants
from pywce.src.models import HookArg
from pywce.src.services import HookService


class HookUtil:
    @staticmethod
    async def process_hook(hook: str, arg: HookArg, external: Optional[Callable] = None) -> HookArg:
        # set hook name here
        arg.hook = hook

        if hook.startswith(EngineConstants.EXT_HOOK_PROCESSOR_PLACEHOLDER) and external is not None:
            if inspect.iscoroutinefunction(external):
                return await external(arg)

            return external(arg)

        return await HookService.process_hook(hook_dotted_path=hook, hook_arg=arg)
