import logging

from pywce import hook, HookArg

logger = logging.getLogger(__name__)

@hook
def save_destination(arg: HookArg) -> HookArg:
    logger.debug(f"Destination hook arg: %s", arg)

    # TODO: assess arg and implement business logic
    #       Data will be available in the arg.additional_data

    return arg
