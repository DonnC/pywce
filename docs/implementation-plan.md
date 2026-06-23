# pywce Implementation Plan

## Scope

> Scope update:
> `pywce` remains WhatsApp-first and WhatsApp-focused.
> The unified multi-channel core will be pursued on the Java-side `jawce` project instead.
> For `pywce`, the active plan is now hardening, test coverage, and a stronger WhatsApp developer experience.

This document converts the architectural evolution plan into an execution-ready plan.

The assumptions for this phase are:

- `WhatsApp` remains the default and first-class supported channel,
- all new custom logic must be introduced through TDD,
- session persistence is not the focus of this phase because the session abstraction is already in place.

## Channel Positioning

`pywce` should remain opinionated and excellent for WhatsApp.

That means:

- the engine can keep WhatsApp-centric abstractions where they are valuable,
- hardening should focus on webhook correctness, session behavior, template behavior, hooks, and message generation,
- broader multi-channel concerns should not distort the Python package architecture.

## Delivery Strategy

The safest delivery sequence is:

1. freeze current WhatsApp behavior with tests,
2. define unified core models,
3. refactor internals behind those models without breaking current usage,
4. improve validation and test coverage around the WhatsApp engine contract.

## Deliverables

This phase should produce:

- a locked-down behavior test suite for the current engine,
- stronger WhatsApp engine and service contracts,
- a clearer WhatsApp-focused architecture baseline for future MCP work,
- a first-pass authoring and verification strategy for Python-side projects using `pywce`.

## Target Architecture Ownership

To keep boundaries clean, each layer should own a narrow responsibility.

## Core Engine Owns

- stage resolution,
- current/previous stage transitions,
- trigger evaluation,
- route matching,
- checkpoint logic,
- inactivity logic,
- hook lifecycle policy,
- prop persistence rules,
- unified outbound intent generation.

## WhatsApp Adapter Owns

- webhook parsing,
- WhatsApp-specific user/message extraction,
- interactive payload formatting,
- media/location/flow specifics,
- actual message send semantics.

## TDD Rule Of Engagement

Every work item should start in this order:

1. write failing tests,
2. confirm the failure represents the intended behavior,
3. implement the smallest change to pass,
4. refactor safely under green tests.

For this project, tests should be written at three levels:

- engine behavior tests,
- adapter contract tests,
- template validation tests.

## Phase-by-Phase Execution

## Phase 1. Characterize the current WhatsApp engine

Goal:
Preserve existing behavior before any architectural refactor.

Tests to add first:

- new user starts at configured start stage,
- existing user resumes current stage,
- button route transitions work,
- text regex route transitions work,
- built-in `menu` goes to start or checkpoint behavior as currently defined,
- built-in `back` returns to previous stage,
- built-in `retry` returns to checkpoint or previous stage based on current rules,
- built-in `report` routes to report stage,
- `prop` fields are saved into session props,
- checkpoint stages are remembered,
- inactivity causes reset behavior,
- stale webhook requests are skipped,
- duplicate message IDs are skipped,
- debounce suppresses rapid duplicate processing,
- `on_receive` is invoked on inbound processing,
- `on_generate` is invoked before outbound generation,
- `router` hook can redirect next stage,
- `template` hook can render dynamic content,
- hook exceptions produce recovery responses,
- invalid user input produces retry/menu/report-style recovery behavior.

Suggested test file grouping:

- `tests/engine/test_engine_flow.py`
- `tests/engine/test_engine_triggers.py`
- `tests/engine/test_engine_hooks.py`
- `tests/engine/test_engine_resilience.py`

## Phase 2. Add WhatsApp adapter contract tests

Goal:
Separate engine behavior from transport behavior.

Tests to add:

- text template maps to `send_message`,
- button template maps to interactive payload,
- list template maps to interactive payload,
- flow template maps to WhatsApp flow payload,
- media template maps to media send,
- location template maps to location send,
- request-location template maps to request-location send,
- unsupported combinations fail clearly.

Suggested test file grouping:

- `tests/adapters/whatsapp/test_inbound_parse.py`
- `tests/adapters/whatsapp/test_outbound_render.py`
- `tests/adapters/whatsapp/test_transport_contract.py`

## Phase 3. Add stronger validation around the WhatsApp flow model

Goal:
Catch authoring mistakes earlier in the WhatsApp-focused template flow.

Tests to write first:

- a flow with a missing next-stage target fails clearly,
- unsupported template kinds fail clearly,
- malformed hooks fail clearly,
- invalid route shapes fail clearly,
- required message fields are enforced by kind.

Suggested test file grouping:

- `tests/validation/test_flow_validation.py`

## Phase 4. Prepare for `**wce` MCP support

Goal:
Make the Python project predictable and inspectable enough for a future MCP that supports both Java and Python `wce` projects well.

Focus areas:

- stable project conventions,
- clearer docs and examples,
- deterministic test harnesses,
- discoverable flow/template structure,
- inspectable hook and template metadata.

## Suggested Initial Test Matrix

This is the first concrete matrix I would implement.

| Area | Behavior | Priority |
|---|---|---|
| Engine | start stage routing | P0 |
| Engine | current stage resume | P0 |
| Engine | button transition | P0 |
| Engine | regex route transition | P0 |
| Engine | built-in triggers | P0 |
| Engine | checkpoint behavior | P0 |
| Engine | prop persistence | P0 |
| Engine | hook ordering | P0 |
| Engine | hook redirect | P0 |
| Engine | invalid input recovery | P0 |
| Engine | stale webhook rejection | P1 |
| Engine | duplicate detection | P1 |
| Engine | debounce behavior | P1 |
| Engine | inactivity reset | P1 |
| Adapter | WhatsApp text render | P0 |
| Adapter | WhatsApp interactive render | P0 |
| Adapter | WhatsApp media render | P1 |
| Validation | flow validation checks | P1 |
| MCP readiness | discoverable project conventions | P2 |

## Recommended First Test Cases To Write

If we were starting immediately, I would write these first five tests before any refactor:

1. `test_new_user_starts_at_configured_start_stage`
2. `test_button_selection_transitions_to_expected_next_stage`
3. `test_menu_trigger_routes_back_to_start_or_checkpoint`
4. `test_on_receive_and_on_generate_run_in_expected_order`
5. `test_invalid_input_returns_recovery_message_without_corrupting_stage`

Then these next five:

1. `test_duplicate_message_id_is_skipped`
2. `test_debounce_blocks_rapid_repeat_processing`
3. `test_template_hook_renders_dynamic_message`
4. `test_router_hook_redirects_next_stage`
5. `test_whatsapp_button_template_renders_interactive_payload`

## Definition Of Done For This Evolution

This phase should be considered successful when:

- the current WhatsApp engine behavior is protected by tests,
- the WhatsApp engine behavior is clearly specified and protected,
- the Python project shape is clean enough to support future `**wce` MCP tooling,
- `pywce` remains strong and focused rather than being stretched into a multi-channel abstraction prematurely.

## Bottom Line

The practical path is:

- keep `pywce` tightly focused on WhatsApp,
- use TDD to preserve and harden today’s behavior,
- improve validation and runtime confidence,
- shape the project so a future `**wce` MCP can serve both Python and Java projects well.

The broader unified multi-channel direction still makes sense, but it now belongs on the Java-side `jawce` effort rather than inside `pywce`.
