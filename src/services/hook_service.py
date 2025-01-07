from src.models import HookArg


class HookService:
    """
        Hook Service:

        Handle hooks from dotted path given.

        Dynamically call hook functions or class methods.
        All hooks should accept a [HookArg] param and return a [HookArg] response.
    """

    @staticmethod
    def process_hook(hook_name: str, hook_arg: HookArg):
        # TODO: implement process hook
        pass
