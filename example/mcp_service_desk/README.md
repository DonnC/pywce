# MCP Service Desk

This example shows a near-real-world WhatsApp support desk bot powered by `pywce` and assisted by `wce-mcp`.

## Why this example

This is a strong first real-world example because it matches a very common business use case:

- customer support or service desk intake,
- structured routing with interactive messages,
- AI-assisted response planning,
- live support escalation,
- rich WhatsApp message types beyond simple text.

It also demonstrates that MCP is useful inside a bot runtime, not only for developers outside the project.

## What it demonstrates

- button and list-based support intake
- dynamic support answer generation through MCP-assisted hooks
- request-location and location confirmation
- media delivery for troubleshooting
- CTA handoff for support escalation
- session props and contextual message rendering

## Suggested environment

- `ENGINE_RUNTIME_MODULE=example.mcp_service_desk.runtime`
- `WCE_MCP_MODE=remote`
- `WCE_MCP_URL=http://127.0.0.1:9000/mcp`

## Recommended MCP transport

Run `wce-mcp` in `streamable-http` mode for this example. That keeps the bot decoupled from the MCP process model and matches how you would wire it to an internal hosted MCP later on.
