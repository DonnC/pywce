from pywce import hook, HookArg, pywce_logger

logger = pywce_logger(__name__)

@hook
def save_destination(arg: HookArg) -> HookArg:
    logger.info(f"Destination hook arg: {arg}")

    # TODO: implement business logic
    # TODO: Data will be available in the arg.additional_data attr

    return arg
