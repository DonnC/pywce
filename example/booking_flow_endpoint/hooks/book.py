from pywce import HookArg, TemplateDynamicBody

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
