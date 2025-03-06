# AI Agents
Create your own customized AI agents.

Inspiration drawn from:
https://github.com/panda-zw/fastapi-whatsapp-openai

## Features
1. Create an AI agent
2. View and chat with any created AI Agent

## Setup
> [!NOTE]
> [Knowledge of & a WhatsApp Flow](https://developers.facebook.com/docs/whatsapp/flows) enabled account is required

Ensure you have your WhatsApp account set properly. [Checkout this tutorial here](https://www.youtube.com/watch?v=Y8kihPdCI_U)

The project uses WhatsApp Flows for the create agent screen.

You can find the example [WhatsApp Flow json here](flows) that you can copy and paste in your project.

Make sure on the `EngineConfig`, you have set `ext_handler_hook` to ai agent processor hook
```python
from pywce import EngineConfig

_eng_config = EngineConfig(
    # .. other fields
    ext_handler_hook="example.ai_agents.hooks.ai_hook.agent_processor"
)
```

## Run
```bash

$ fastapi dev main.py
```

