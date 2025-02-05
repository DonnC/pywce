from pywce import hook, HookArg
from pywce.src.utils.engine_logger import pywce_logger

logger = pywce_logger(__name__)

@hook
def save_destination(arg: HookArg) -> HookArg:
    logger.info(f"Destination hook arg: {arg}")

    # TODO: assess arg and implement business logic
    #       Data will be available in the arg.additional_data

    return arg
