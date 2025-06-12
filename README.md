# WhatsApp ChatBot Engine

A framework for creating WhatsApp chatbots of any scale using a template-driven approach - 
allowing you to define conversation flows and business logic in a clean and modular way. 

> [!NOTE]
> Template engine and WhatsApp client library are decoupled - allowing you to use them independently or together. 


## Features

- **Template-Driven Design**: Use templates (YAML by default) for conversational flows.
- **Hooks for Business Logic**: Attach Python functions to process messages or actions.
- Focus on your conversation flow and business logic.
- Easy-to-use API for WhatsApp Cloud.
- Model based templates
- Supports dynamic messages with placeholders.
- Built-in support for WhatsApp Webhooks.
- *Support WhatsApp Flow endpoint
- Starter templates

## Installation
```bash
pip install git+https://github.com/DonnC/pywce.git@sync
```


---

## Why pywce
Most WhatsApp chatbot tutorials or libraries just scraps the surface, only sending a few message or handling simple logic or are client libraries only.

This library gives you a full-blown framework for chatbots of any scale allowing you access to full package of whatsapp client library and chatbot development framework.

---

## Setup

### Summary: Setup in 6 easy steps (with FastAPI)
1. Clone repo and navigate to the `example` folder
2. Install all dependencies 
3. Setup your whatsapp account configs in `.env.example` and edit the file to `.env` only
4. Run the `main.py` and setup tunnelling using `ngrok` or any similar service and configure your webhook on developer portal
5. Build on top of the example templates in `example\ehailing\templates` folder to suit your chatbot needs
6. Implement your chatbot logic in `example\ehailing\hooks` folder

> After you get the hang of it, you can start your new project afresh
---

### WhatsApp
Follow the complete step by step WhatsApp Cloud API guide below. 

[![WhatsApp Cloud API Complete Setup Guide](https://img.youtube.com/vi/Y8kihPdCI_U/0.jpg)](https://www.youtube.com/watch?v=Y8kihPdCI_U)

Important settings needed for this framework
1. Phone number ID (be it test number or live number)
2. Access Token (Temporary or permanent)
3. Webhook callback verification token of your choice
4. App secret (optional)

### Engine
You can either use `.env` or add your credentials directly to the WhatsAppConfig class

```python
import os
from dotenv import load_dotenv
from pywce import client, Engine, EngineConfig, storage

load_dotenv()

# configure default YAML/JSON templates manager
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

engine_instance = Engine(config=engine_config)
```

## Example ChatBot
Here's a simple example template to get you started:

> [!NOTE]
> _Checkout complete working examples in the [example folder](https://github.com/DonnC/pywce/blob/master/example)_


1. Define YAML/JSON template (Conversation Flow💬):

```yaml
# path/to/templates
"START-MENU":
  type: button
  template: "path.to.func.username"
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
  message: Great, lets get you started quickly. What is your age?
  routes:
    "re://d{1,}": "ANOTHER-STEP"
```

2. Write your hook (Supercharge⚡):
```python
# path/to/func.py
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

Use `fastapi` or `flask` or any python library to create endpoint to receive whatsapp webhooks

```python
# ~ fastapi snippet ~

def webhook_event(payload: dict, headers: dict) -> None:
    """
    Process webhook event in the background using pywce engine.
    """
    engine_instance.process_webhook(payload, headers)

@app.post("/chatbot/webhook")
async def process_webhook(req: Request, bt: BackgroundTasks):
    """
    Handle incoming webhook events from WhatsApp 
    and process them in the background.
    """
    payload = await req.json()
    headers = dict(req.headers)

    # handle webhook in the background
    bt.add_task(webhook_event, payload, headers)

    return Response(content="ACK", status_code=200)
```

### Run ChatBot
If you run your project or the example projects successfully, your webhook url will be available on `localhost:port/chatbot/webhook`.

_You can use `ngrok` or any service to tunnel your local service_

You can then configure the endpoint in Webhook section on  Meta developer portal.

## WhatsApp Client Library
> [!NOTE]
> _You can use pywce as a standalone whatsapp client library. See [Example](https://github.com/DonnC/pywce/blob/master/example/chatbot)_

PyWCE provides a simple, Pythonic interface to interact with the WhatsApp Cloud API:

- **Send messages** (text, media, templates, interactive)
- **Receive and process webhooks**
- **Media management** (upload and download)
- **Out of the box utilities** using the `WhatsApp.Utils` class.

Example usage:

```python
from pywce import client

config = client.WhatsAppConfig(
    token="your_access_token",
    phone_number_id="your_phone_number_id",
    hub_verification_token="your_webhook_hub_verification_token"
)

whatsapp = client.WhatsApp(whatsapp_config=config)

# Sending a text message
response = whatsapp.send_message(
    recipient_id="recipient_number",
    message="Hello from PyWCE!"
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
