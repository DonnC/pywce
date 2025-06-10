import logging

from pywce import HookArg

logger = logging.getLogger(__name__)

def save_destination(arg: HookArg) -> HookArg:
    # TODO: implement business logic
    #       Data will be available in the arg.additional_data

    return arg
