from pywce import HookArg, TemplateDynamicBody

from example.common.mcp_client import call_wce_mcp_tool


def render_assist_answer(arg: HookArg) -> HookArg:
    issue = arg.session_manager.get_from_props(arg.session_id, "support_issue") or str(arg.user_input or "")
    runtime_plan = call_wce_mcp_tool(
        "plan_ai_runtime",
        {"bot_goal": issue, "runtime": "pywce"},
    )

    strategy = call_wce_mcp_tool(
        "recommend_message_strategy",
        {"goal": issue, "input_expected": "mixed", "ai_mode": "assistant"},
    )
    handoff = call_wce_mcp_tool(
        "plan_live_support_handoff",
        {"bot_goal": issue, "handoff_trigger": "user_requested_or_issue_sensitive"},
    )

    summary = issue if len(issue) < 120 else issue[:117] + "..."
    guardrail = runtime_plan["guardrails"][0] if runtime_plan.get("guardrails") else "Keep sensitive actions deterministic."
    recommendation = strategy["recommended_types"][0] if strategy.get("recommended_types") else "text"
    arg.template_body = TemplateDynamicBody(
        render_template_payload={
            "summary": summary,
            "strategy": ", ".join(strategy["recommended_types"][:3]),
            "escalation": handoff["handoff_strategy"][0],
            "guardrail": guardrail,
            "recommendation": recommendation,
        }
    )
    return arg
