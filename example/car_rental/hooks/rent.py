import re
from datetime import datetime, timedelta

from pywce import HookArg, pywce_logger, hook, TemplateDynamicBody
from ..service.rental_service import CarRentalService

logger = pywce_logger(__name__)

service = CarRentalService()

TEMP_DATA_SESSION_KEY = "temp_data"

def extract_cost(metadata: str):
    match = re.search(r"\d+\.\d+", metadata)
    return float(match.group()) if match else 0


@hook
def init_rental(arg: HookArg):
    """
    init_rental(arg: HookArg)

    Initialize the rent a car flow. The flow requires data to be passed in.

    Args:
        arg (HookArg): pass hook argument from engine

    Returns:
        HookArg: the passed hook argument
    """
    min_date = datetime.today().strftime("%Y-%m-%d")
    max_date = (datetime.today() + timedelta(days=service.get_rental_duration())).strftime("%Y-%m-%d")

    flow_data = {
        "min_date": min_date,
        "max_date": max_date,
        # "packages": service.packages()
    }

    arg.template_body = TemplateDynamicBody(initial_flow_payload=flow_data)

    return arg


@hook
def quote(arg: HookArg):
    """
    quote(arg: HookArg)

    Compute car rental quotation from given customer data.

    Create a message body to user for confirmation.

    Args:
         arg (HookArg): passed hook argument from engine

    Returns:
         HookArg: the passed / updated hook argument
    """
    logger.debug(f"Quote car rental arg: {arg}")

    # engine sets the returned flow response into additional data
    data = arg.additional_data
    period = data["period"]

    package = service.get_package_by_id(data.get("car"))

    start_date = datetime.strptime(period.get('start-date'), "%Y-%m-%d")
    end_date = datetime.strptime(period.get('end-date'), "%Y-%m-%d")

    rental_days = (end_date - start_date).days + 1
    daily_cost = extract_cost(package.get("metadata"))
    extras = ", ".join(data.get('extras', ['-']))

    confirmation = f"""Details
    Name: {data.get('fullname')}
    ID: {data.get('id_number')}
    Car: {package.get('title')}
    Extras: {extras}
    Duration: {rental_days} Days
    Cost: {package.get('metadata')}
    ______________
    
    Total: ${service.calculate_rental_charges(rental_days, daily_cost)}
    """

    # create payload to save later
    rental_payload = {
        "mobile": arg.session_id,
        "car": package.get('title'),
        "fullname": data.get('fullname'),
        "id_number": data.get('id_number'),
        "start_date": period.get('start-date'),
        "end_date": period.get('end-date'),
        "extras": extras,
        "total_days": rental_days,
        "charges": service.calculate_rental_charges(rental_days, daily_cost)
    }

    # create needed templates body to render
    render_payload = {"body": confirmation}

    # save arbitrary data to user session
    # may be used later when saving to db & processing payment
    arg.session_manager.save(arg.session_id, TEMP_DATA_SESSION_KEY, rental_payload)

    arg.template_body = TemplateDynamicBody(render_template_payload=render_payload)

    return arg


@hook
def customer_rentals(arg: HookArg):
    """
    customer_rentals(arg: HookArg)

    Fetch all current running customer rentals.

    Args:
         arg (HookArg): passed hook argument from engine

    Returns:
         HookArg: the passed / updated hook argument
    """

    rentals = service.retrieve_user_rentals(arg.session_id)

    logger.debug(f"Customer rentals: {rentals}")

    if len(rentals) == 0:
        message = "You have no car rentals. Book one with us!"

    else:
        message = "My rental history:\n\n"
        for rental in rentals:
            message += "\n"
            message += f"Car: {rental.get('car')}\n"
            message += f"Starting: {rental.get('start_date')}\n"
            message += f"End: {rental.get('end_date')}\n"
            message += f"Extras: {rental.get('extras')}\n"
            message += f"Days: {rental.get('total_days')}\n"
            message += f"_________\n"

    message.strip()
    message += "\n\nType menu to return to Menu"

    render_payload = {"body": message}

    arg.template_body = TemplateDynamicBody(render_template_payload=render_payload)

    return arg
