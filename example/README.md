# Examples
A curated list of example chatbots developed using the pywce library.

> [!NOTE]
> The example projects uses [Fast Api](https://fastapi.tiangolo.com/)


## Demo
Checkout curated playlist of these examples on YouTube

[![Pywce playlist](https://img.youtube.com/vi/Y8kihPdCI_U/0.jpg)](https://www.youtube.com/watch?v=Y8kihPdCI_U)


## Setup
The examples have all have the same structure in [common directory](common)

To run the bots, add the `.env` file (view the example [.env.example](.env.example) file) to add your configs.

Install project dependencies
```bash
pip install -r requirements.txt
```

For the MCP-backed examples, also run `wce-mcp` as a separate service. The recommended local mode is `streamable-http` because it behaves like a deployed MCP service while still being easy to test locally:

```bash
cd ../wce-mcp
.\.venv\Scripts\python.exe -m wce_mcp --transport streamable-http --host 127.0.0.1 --port 9000
```

Then point the example app at it with:

```bash
WCE_MCP_MODE=remote
WCE_MCP_URL=http://127.0.0.1:9000/mcp
```

The example app can also load a custom runtime module so each bot can own its own storage and engine wiring:

```bash
ENGINE_RUNTIME_MODULE=example.mcp_service_desk.runtime
```

## New Real-World Examples

### `mcp_service_desk`

Why this example:

- It mirrors one of the most common production WhatsApp use cases: support intake and escalation.
- It shows how `pywce` can use `wce-mcp` inside hooks to improve response planning and support orchestration.
- It demonstrates rich message types including buttons, lists, request-location, location, media, and CTA.
- It works well as the first realistic reference for a later AI-assisted service or operations bot.

### `self_evolving_support_bot`

Why this example:

- It demonstrates the controlled self-evolving bot pattern you are aiming for.
- It uses MCP-generated assets, activation manifests, and recursive template loading instead of unsafe engine mutation.
- It shows a practical path toward AI-assisted runtime evolution while keeping guardrails in place.
- It is the best stepping stone toward a future autonomous support bot that can safely extend itself.

## Support
Thank you, if you like or find my work helpful to you.
Your support goes a long way in taking this work further, be it sharing with your network, staring the repository, 
contributing or even financial support - I appreciate any form of support.

or get in touch with me on [donnclab@gmail.com](mailto:donychinhuru@gmail.com)

Want a chatbot developed for you or just to say hi or get in touch on software development projects or consultancy?
You can contact me on the email above.
