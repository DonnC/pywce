# WhatsApp ChatBot Engine

A framework for creating complete WhatsApp chatbots of any scale using a template-driven approach - 
allowing you to define conversation flows and business logic in a clean and modular way. 

> [!NOTE]
> Core chatbot template engine and WhatsApp client library are decoupled - allowing you to use them independently or together. 


## Features

- **Template-Driven Design**: Define conversational flows and business logic in a clean, modular way (Support YAML & JSON templates by default).
- **Hooks for Business Logic**: Attach Python functions to process messages or actions on your hooks.
- **Customizable**: implement your own session & template storage source.
- Easy-to-use API for WhatsApp Cloud.
- Supports dynamic messages with placeholders.
- Built-in support for common chatbot input phrases like `back`, `retry`, `report` and `menu`. Also caches default name under `wa_name` key
- Support WhatsApp Flow endpoint
- Supports all WhatsApp message types

## Installation
```bash
pip install git+https://github.com/DonnC/pywce.git
```

---

## Why pywce
Most WhatsApp chatbot tutorials or libraries acts as client libraries only or give basic chatbot using a lot of `if..else`.

This project gives you a complete approach for developing chatbots of any scale, giving you access to full package of whatsapp client library and chatbot development framework.

---

## Setup

### Summary: Setup in 6 easy steps (with FastAPI)
1. Clone repo and install all dependencies, `pip install .`
2. Navigate to the `example` folder and install its dependencies too, `pip install -r requirements.txt`
3. Setup your whatsapp account configs in `.env.example` and edit the file to `.env` only
4. Run the chatbot, `fastapi dev main.py` and setup tunneling using `ngrok` or any similar service (if hosted local) and configure your webhook on developer portal
5. Build on top of available example templates in `example/` folder to suit your chatbot needs
6. Implement your chatbot logic in `example/<project-name>/hooks` folder

> After you get the hang of it, you can start your new project afresh
---

### WhatsApp
Follow the complete step by step WhatsApp Cloud API guide below. 

[![WhatsApp Cloud API Complete Setup Guide](https://img.youtube.com/vi/Y8kihPdCI_U/0.jpg)](https://www.youtube.com/watch?v=Y8kihPdCI_U)

Important settings needed for this library
1. Phone number ID
2. Access Token
3. Webhook callback verification token of your choice
4. App secret

### Engine
You can either use `.env` or add your credentials directly to the WhatsAppConfig class

```python
# config.py
import os
from dotenv import load_dotenv
from pywce import client, Engine, EngineConfig, storage

load_dotenv()

# configure default YAML/JSON templates source
template_storage_manager = storage.YamlJsonStorageManager(
    os.getenv("TEMPLATES_DIR"),
    os.getenv("TRIGGERS_DIR")
)

whatsapp_config = client.WhatsAppConfig(
    token=os.getenv("ACCESS_TOKEN"),
    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
    hub_verification_token=os.getenv("WEBHOOK_HUB_TOKEN")
)

whatsapp = client.WhatsApp(whatsapp_config=whatsapp_config)

engine_config = EngineConfig(
    whatsapp=whatsapp,
    storage_manager=template_storage_manager,
    start_template_stage=os.getenv("START_STAGE")
)

engine = Engine(config=engine_config)
```

## Example ChatBot
Here's a simple example template to get you started:

> [!NOTE]
> _Checkout complete working examples in the [example folder](https://github.com/DonnC/pywce/blob/master/example)_


1. Define YAML/JSON template (Conversation Flow💬):

```yaml
# path/to/templates/bot.yaml
"START-MENU":
  type: button
  template: "path.to.hook.username"
  message:
    title: Welcome
    body: "Hi {{ name }}, I'm your assistant, click below to start!"
    footer: pywce
    buttons:
      - Start
  routes:
    "start": "NEXT-STEP"

"NEXT-STEP":
  type: text
  prop: age
  message: Great, What is your age?
  routes:
    "re:.*": "ANOTHER-STEP"
```

2. Write your hook (Supercharge⚡):
```python
# path/to/hook.py
from pywce import HookArg, TemplateDynamicBody

def username(arg: HookArg) -> HookArg:
    """
     fill message template's dynamic variable: name
     to greet user by their whatsapp name 😎
    """
    
    template_value = {"name": arg.user.name}
    
    arg.template_body = TemplateDynamicBody(
        render_template_payload=template_value
    )

    return arg
```

3. Engine client:

Use `fastapi` or `flask` or any python library to create endpoint to receive WhatsApp webhooks

```python
# main.py

# ~ fastapi snippet ~

from .config import engine, whatsapp

def bg_wehbook_handler(payload: dict, headers: dict) -> None:
    engine.process_webhook(payload, headers)

@app.post("/chatbot/webhook")
async def process_webhook(req: Request, bg_task: BackgroundTasks):
    """
        Handle incoming webhook events from WhatsApp 
        and process them in the background.
    """
    payload = await req.json()

    bg_task.add_task(bg_wehbook_handler, payload, dict(req.headers))
    
    return Response(content="ACK", status_code=200)
```

## WhatsApp Client Library
> [!NOTE]
> _You can use pywce as a standalone whatsapp client library. See [Example](https://github.com/DonnC/pywce/blob/master/example/chatbot)_

PyWCE provides a simple, Pythonic interface to interact with the WhatsApp Cloud API:

- **Send messages** (text, media, templates, interactive, etc)
- **Receive and process webhooks**
- **Media management** (upload and download)
- **Out of the box utilities** using the `WhatsApp.Utils` class.

Example usage:

```python
from pywce import client

config = client.WhatsAppConfig(
    token="ACCESS-TOKEN",
    phone_number_id="PHONE-NUMBER-ID",
    hub_verification_token="WEBHOOK-VERIFICATION-TOKEN"
)

whatsapp = client.WhatsApp(whatsapp_config=config)

# Sending a text message
response = whatsapp.send_message(
    recipient_id="recipient_number",
    message="Hello from pywce!"
)

# verify if request was successful, using utils
is_sent = whatsapp.util.was_request_successful(
    recipient_id="recipient_number",
    response_data=response
)

if is_sent:
    message_id = whatsapp.util.get_response_message_id(response)
    print("Request successful with msg id: ", message_id)
```


## Documentation

Visit the [official documentation](https://docs.page/donnc/wce) for a detailed guide.

## Changelog

Visit the [changelog list](https://github.com/DonnC/pywce/blob/master/CHANGELOG.md)  for a full list of changes.

## Contributing

We welcome contributions! Please check out the [Contributing Guide](https://github.com/DonnC/pywce/blob/master/CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/DonnC/pywce/blob/master/LICENCE) file for details.
