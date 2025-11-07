from example.common.data import LocalDataSource
from pywce import HookArg, TemplateDynamicBody

def get_available_booking_slots(arg: HookArg) -> HookArg:
    """
        Get available booking slots dynamically
        To use as initial flow data
    """
    # TODO: fetch from DB

    flow_data = {
        "time_slots": LocalDataSource.available_booking_slots,
        "is_dropdown_visible": False
    }

    arg.template_body = TemplateDynamicBody(flow_payload=flow_data)

    return arg

def save_render_booking(arg: HookArg) -> HookArg:
    """
        Saves a user booking details filled from flow and
        render confirmation flow using flow data
    """

    # TODO: Save details
    form_data = arg.additional_data

    template_data = {
        "username": f"{form_data['first_name']} {form_data['last_name']}",
        "national_id": form_data["national_id"],
        "birth_date": form_data["birth_date"],
        "time_slot": str(form_data.get("time_slot")).replace("_", ":") + " hrs"
    }

    arg.template_body = TemplateDynamicBody(render_template_payload=template_data)

    return arg
