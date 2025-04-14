from typing import Optional, Callable

from pywce.src.constants import EngineConstants
from pywce.src.models import HookArg
from pywce.src.services import HookService


class HookUtil:
    @staticmethod
    def process_hook(hook: str, arg: HookArg, external: Optional[Callable] = None) -> HookArg:
        # set hook name here
        arg.hook = hook

        if hook.startswith(EngineConstants.EXT_HOOK_PROCESSOR_PLACEHOLDER) and external is not None:
            return external(arg)

        return HookService.process_hook(hook_dotted_path=hook, hook_arg=arg)

    @staticmethod
    def run_listener(listener: Optional[Callable] = None, arg: Optional[HookArg] = None) -> None:
        try:
            if listener is not None:
                if arg is not None:
                    listener(arg)
                else:
                    listener()

        except Exception as e:
            print("[LISTENER-ERROR] Failed to process listener: ", str(e))