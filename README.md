# WhatsApp ChatBot Engine

A framework for creating WhatsApp chatbots of any scale using a template-driven approach - 
allowing you to define conversation flows and business logic in a clean and modular way. 

> [!NOTE]
> Template engine and WhatsApp client library are decoupled - allowing you to use them independently or together. 


## Features

- **Template-Driven Design**: Use YAML templates for conversational flows.
- **Hooks for Business Logic**: Attach Python functions to process messages or actions.
- Focus on your conversation flow and business logic.
- Easy-to-use API for WhatsApp Cloud.
- Supports dynamic messages with placeholders.
- Built-in support for WhatsApp Webhooks.
- Starter templates
- Live Support / Human interaction portal template

## Installation
```bash

pip install pywce
```


---

## Why pywce
Most WhatsApp chatbot tutorials or libraries just scraps the surface, only sending a few message or handling simple logic or are client libraries only.

This library gives you a full-blown framework for chatbots of any scale allowing you access to full package of whatsapp client library and chatbot development framework.

---

## Setup
### WhatsApp
Follow the complete step by step WhatsApp Cloud API guide below. 

[![WhatsApp Cloud API Complete Setup Guide](https://img.youtube.com/vi/Y8kihPdCI_U/0.jpg)](https://www.youtube.com/watch?v=Y8kihPdCI_U)

Important settings needed for this framework
1. Phone number ID (be it test number or live number)
2. Access Token (Temporary or permanent)
3. Webhook callback verification token of your choice

Create a `.env `with the below settings in your project or test folder (be it `example` or `portal` folders)

```
ACCESS_TOKEN        = <your-whatsapp-access-token>
PHONE_NUMBER_ID     = <your-number-phone-id>
WEBHOOK_HUB_TOKEN   = <your-webhook-verification-token>

# path to your templates & triggers folders
TEMPLATES_DIR       = portal/chatbot/templates
TRIGGERS_DIR        = portal/chatbot/triggers

# your templates initial or start stage
START_STAGE         = START-MENU
```

### Engine
You can either use `.env` or add your credentials directly to the WhatsAppConfig class
```python
import os
from dotenv import load_dotenv
from pywce import client, Engine, EngineConfig

load_dotenv()

whatsapp_config = client.WhatsAppConfig(
    token=os.getenv("ACCESS_TOKEN"),
    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
    hub_verification_token=os.getenv("WEBHOOK_HUB_TOKEN")
)

whatsapp = client.WhatsApp(whatsapp_config=whatsapp_config)

engine_config = EngineConfig(
    whatsapp=whatsapp,
    templates_dir=os.getenv("TEMPLATES_DIR"),
    trigger_dir=os.getenv("TRIGGERS_DIR"),
    start_template_stage=os.getenv("START_STAGE")
)

engine_instance = Engine(config=engine_config)
```

## Example ChatBot
Here's a simple example template to get you started:

> [!NOTE]
> _Checkout complete working examples in the [example folder](https://github.com/DonnC/pywce/blob/master/example)_


1. Define YAML template (Conversation Flow💬):

```yaml
# path/to/templates
"START-MENU":
  type: button
  template: "example.hooks.name_template.username"
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
    "re://d{1,}": "NEXT-STEP-FURTHER"
```

2. Write your hook (Supercharge⚡):
```python
# example/hooks/name.py
from pywce import hook, HookArg, TemplateDynamicBody

@hook
def username(arg: HookArg) -> HookArg:
    # set render payload data to match the required templates dynamic var
    
    # greet user by their whatsapp name 😎
    arg.template_body = TemplateDynamicBody(
        render_template_payload={"name": arg.user.name}
    )

    return arg
```

3. Engine client:

Use `fastapi` or `flask` or any python library to create endpoint to receive whatsapp webhooks

```python
# ~ fastapi snippet ~

async def webhook_event(payload: Dict, headers: Dict) -> None:
    """
    Process webhook event in the background using pywce engine.
    """
    await engine_instance.process_webhook(payload, headers)

@app.post("/chatbot/webhook")
async def process_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming webhook events from WhatsApp 
    and process them in the background.
    """
    payload = await request.json()
    headers = dict(request.headers)

    # handle event in the background
    background_tasks.add_task(webhook_event, payload, headers)

    # Immediately respond to WhatsApp with acknowledgment
    return Response(content="ACK", status_code=200)
```

### Run ChatBot
If you run your project or the example projects successfully, your webhook url will be available on `localhost:port/chatbot/webhook`.

_You can use `ngrok` or any service to tunnel your local service_

You can then configure the endpoint in Webhook section on  Meta developer portal.

## Live Support 
Engine comes with a default basic live support /  human interaction portal out-of-the-box powered by [Reflex](https://reflex.dev/)

Check out [Live Support Portal](https://github.com/DonnC/pywce/tree/feat/live-support/portal)

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
