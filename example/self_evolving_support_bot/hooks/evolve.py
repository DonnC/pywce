from pathlib import Path

from pywce import HookArg, TemplateDynamicBody, template

from example.common.mcp_client import call_wce_mcp_tool


EXAMPLE_ROOT = Path(__file__).resolve().parents[1]


def route_request(arg: HookArg) -> HookArg:
    question = str(arg.user_input or "").strip()
    status = call_wce_mcp_tool("get_generated_asset_status", {"root_path": str(EXAMPLE_ROOT)})

    normalized = question.lower()
    for asset_path in status["active_assets"]:
        asset_name = Path(asset_path).stem.replace("-", " ").replace("_", " ")
        if asset_name in normalized:
            stage = Path(asset_path).stem.upper().replace("_", "-")
            arg.session_manager.save_prop(arg.session_id, "known_topic", asset_name)
            arg.session_manager.save_prop(arg.session_id, "known_response", f"I found an active generated capability for {asset_name}.")
            arg.redirect_to = "KNOWN-RESPONSE"
            return arg

    if any(keyword in normalized for keyword in ["refund", "password", "booking", "delivery"]):
        arg.session_manager.save_prop(arg.session_id, "known_topic", question)
        arg.session_manager.save_prop(
            arg.session_id,
            "known_response",
            "This looks like a known support topic. In a production bot, a deterministic or AI support service would answer here.",
        )
        arg.redirect_to = "KNOWN-RESPONSE"
        return arg

    arg.session_manager.save(arg.session_id, "pending_skill_request", question)
    draft_new_skill(arg)
    arg.redirect_to = "DRAFT-RESULT"
    return arg


def draft_new_skill(arg: HookArg) -> HookArg:
    request = str(arg.user_input or arg.session_manager.get_from_props(arg.session_id, "skill_request") or "").strip()
    stage_name = request.split(" ")[0].upper().replace("/", "-") if request else "NEW-CAPABILITY"
    strategy = call_wce_mcp_tool("plan_self_modification_strategy", {"runtime": "pywce"})

    template_asset = call_wce_mcp_tool(
        "draft_template_asset",
        {
            "stage_name": stage_name,
            "purpose": request or "Generated support capability",
            "kind": "text",
        },
    )
    hook_asset = call_wce_mcp_tool(
        "draft_hook_asset",
        {
            "hook_name": stage_name.lower().replace("-", "_"),
            "responsibility": f"Handle generated support capability for: {request}",
            "runtime": "pywce",
        },
    )

    pending_assets = [template_asset, hook_asset]
    validation = call_wce_mcp_tool("validate_generated_assets", {"files": pending_assets})
    arg.session_manager.save(arg.session_id, "pending_assets", pending_assets)
    arg.session_manager.save(arg.session_id, "pending_summary", request or "Generated support capability")
    arg.session_manager.save(arg.session_id, "pending_validation", validation)
    arg.session_manager.save(
        arg.session_id,
        "pending_guardrail",
        strategy["guardrails"][0] if strategy.get("guardrails") else "Generated assets should stay outside core engine code.",
    )
    return arg


def render_draft_result(arg: HookArg) -> HookArg:
    pending_assets = arg.session_manager.get(arg.session_id, "pending_assets") or []
    summary = arg.session_manager.get(arg.session_id, "pending_summary") or "No draft prepared"
    validation = arg.session_manager.get(arg.session_id, "pending_validation") or {"valid": False, "issues": []}
    guardrail = arg.session_manager.get(arg.session_id, "pending_guardrail") or "No guardrail selected."
    asset_lines = "\n".join(f"- {asset['path']}" for asset in pending_assets) if pending_assets else "- none"
    validation_summary = "valid" if validation.get("valid") else "; ".join(validation.get("issues", [])) or "invalid"

    arg.template_body = TemplateDynamicBody(
        render_template_payload={
            "summary": summary,
            "assets": asset_lines,
            "validation": validation_summary,
            "guardrail": guardrail,
        }
    )
    return arg


def activate_draft(arg: HookArg) -> HookArg:
    pending_assets = arg.session_manager.get(arg.session_id, "pending_assets") or []
    if not pending_assets:
        return arg

    validation = call_wce_mcp_tool("validate_generated_assets", {"files": pending_assets})
    if not validation.get("valid"):
        arg.session_manager.save_prop(
            arg.session_id,
            "known_response",
            "Draft activation stopped because the generated assets failed validation.",
        )
        arg.session_manager.save_prop(arg.session_id, "known_topic", "generated asset validation")
        arg.redirect_to = "KNOWN-RESPONSE"
        return arg

    call_wce_mcp_tool(
        "write_generated_assets",
        {
            "destination_root": str(EXAMPLE_ROOT),
            "files": pending_assets,
        },
    )
    call_wce_mcp_tool(
        "activate_generated_assets",
        {
            "root_path": str(EXAMPLE_ROOT),
            "asset_paths": [asset["path"] for asset in pending_assets],
        },
    )

    from example.self_evolving_support_bot.runtime import storage_manager

    storage_manager.load_templates()
    storage_manager.load_triggers()
    storage_manager.validate()
    return arg


def render_known_response(arg: HookArg) -> HookArg:
    topic = arg.session_manager.get_from_props(arg.session_id, "known_topic") or "support topic"
    response = arg.session_manager.get_from_props(arg.session_id, "known_response") or "No known response available."
    source = "generated asset, validation path, or known support rule"
    arg.template_body = TemplateDynamicBody(
        render_template_payload={
            "topic": topic,
            "response": response,
            "source": source,
        }
    )
    return arg


def list_generated_assets_template(arg: HookArg) -> HookArg:
    payload = call_wce_mcp_tool("list_generated_assets", {"root_path": str(EXAMPLE_ROOT)})
    asset_names = payload["assets"] if payload["exists"] else []

    if not asset_names:
        dynamic_template = template.ButtonTemplate(
            message=template.ButtonMessage(
                title="Generated Assets",
                body="No generated assets have been written yet.",
                buttons=["Menu"],
            ),
            routes=[template.EngineRoute(user_input="menu", next_stage="START-MENU")],
        )
    else:
        dynamic_template = template.ListTemplate(
            message=template.ListMessage(
                title="Generated Assets",
                body="These are the currently generated files known to the bot.",
                button="View Assets",
                sections={
                    "Generated Assets": {
                        str(index): {"title": asset_name, "description": "generated asset"}
                        for index, asset_name in enumerate(asset_names[:10], start=1)
                    }
                },
            ),
            routes=[template.EngineRoute(user_input="re:.*", next_stage="START-MENU", is_regex=True)],
        )

    arg.template_body = TemplateDynamicBody(dynamic_template=dynamic_template)
    return arg
