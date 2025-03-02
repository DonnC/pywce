from pywce import HookArg, pywce_logger, hook

from .rent import TEMP_DATA_SESSION_KEY
from ..service.rental_service import CarRentalService

logger = pywce_logger(__name__)

service = CarRentalService()


@hook
def initiate(arg: HookArg):
    """
    initiate(arg: HookArg)

    TODO: implement initiate payment request

    Args:
        arg (HookArg): pass hook argument from engine

    Returns:
        HookArg: the passed hook argument
    """

    # Use any payment gateway to initiate payment request
    # and process properly

    # save rental to db
    logger.info("Saving rental request..")

    data = arg.session_manager.get(arg.session_id, TEMP_DATA_SESSION_KEY)

    service.save_rental_request(data)

    logger.info("Rental request saved!")

    return arg
