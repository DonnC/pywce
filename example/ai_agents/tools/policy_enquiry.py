from pywce import pywce_logger

logger = pywce_logger(__name__)


def policy_enquiry(policy_number: str):
    """
    Call this tool when user wants to enquire about their policy number.

    Args:
        policy_number (str): Customer's policy number.

    Returns:
        str: The customer policy details
    """

    logger.debug("== policy_enquiry ==> tool called")

    return f"""{policy_number}
    
    First Name: John
    Last Name: Doe
    Email: jdoe@pywce.ai
    Mobile Number: +263770123456
    Address: 404 jdoe street
    Registered On: 23 Sept 2013
    """
