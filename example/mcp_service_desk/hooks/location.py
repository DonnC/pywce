from pywce import HookArg, TemplateDynamicBody


def capture_shared_location(arg: HookArg) -> HookArg:
    payload = arg.additional_data or {}
    if payload:
        arg.session_manager.save_prop(arg.session_id, "shared_location", payload)
    return arg


def render_shared_location(arg: HookArg) -> HookArg:
    payload = arg.session_manager.get_from_props(arg.session_id, "shared_location") or {}
    lat = str(payload.get("latitude", "-17.8252"))
    lon = str(payload.get("longitude", "31.0335"))
    name = payload.get("name") or "Shared support location"
    address = payload.get("address") or "Location supplied by user"

    arg.template_body = TemplateDynamicBody(
        render_template_payload={
            "lat": lat,
            "lon": lon,
            "name": name,
            "address": address,
        }
    )
    return arg

