from pywce import hook, HookArg
from ..service.rental_service import CarRentalService


@hook
def save(arg: HookArg) -> HookArg:
    """
    save(arg)

    This hook will save a customer rented car report issue or enquiry

    Args:
        arg (HookArg): pass hook argument from engine

    Returns:
        HookArg: the passed hook argument
    """
    service = CarRentalService()

    report_or_enquiry = arg.session_manager.get_from_props(arg.session_id, "report_enquiry")

    if arg.params.get('type', 'REPORT') == 'REPORT':
        service.save_rental_issue(
            mobile=arg.session_id,
            issue=report_or_enquiry
        )
    else:
        service.save_user_enquiry(
            mobile=arg.session_id,
            enquiry=report_or_enquiry
        )

    return arg
