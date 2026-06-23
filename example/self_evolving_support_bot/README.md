# Self Evolving Support Bot

This example shows a controlled self-evolving `pywce` bot that uses `wce-mcp` to draft, write, activate, and inspect generated bot assets.

## Why this example

This is the best near-real-world example for the self-evolving direction because it demonstrates:

- controlled runtime extension instead of unsafe engine mutation,
- generated templates and hooks,
- activation manifests,
- recursive template loading for generated assets,
- AI-ready extension points that can be reviewed and rolled back.

It is intentionally opinionated about safety: the bot evolves through generated assets and manifests, not by rewriting core engine code.

## What it demonstrates

- dynamic route decisions
- MCP-generated template and hook assets
- generated asset manifests and activation flow
- recursive template loading for generated content
- list-based visibility into learned/generated capabilities

## Suggested environment

- `ENGINE_RUNTIME_MODULE=example.self_evolving_support_bot.runtime`
- `WCE_MCP_MODE=remote`
- `WCE_MCP_URL=http://127.0.0.1:9000/mcp`

## Recommended MCP transport

Run `wce-mcp` in `streamable-http` mode for this example. This lets the bot behave as if the MCP is already deployed remotely, while still allowing you to host it on `localhost` during development.
