# Python WhatsApp ChatBot Engine

A framework for creating WhatsApp chatbots using a template-driven approach - 
allowing you to define conversation flows and business logic in a clean and modular way. 

It decouples the engine from the WhatsApp client library, allowing developers to use them independently or together. 

## Features

- **Template-Driven Design**: Use YAML templates for conversational flows.
- **Hooks for Business Logic**: Attach Python functions to process messages or actions.
- Easy-to-use API for WhatsApp Cloud.
- Supports dynamic messages with placeholders.
- Built-in support for WhatsApp Webhooks.


## Installation
```bash
pip install pywce
```

## Why pywce
Most "WhatsApp ChatBots" tutorials or libraries just scraps the surface, only sending a few message or handling simple logic.

This library gives you a full-blown framework for chatbots of any scale.

### WhatsApp Client Library

PyWCE provides a simple, Pythonic interface to interact with the WhatsApp Cloud API:

_**Note**: You can use pywce as a standalone whatsapp client library. See [FastApi Example](https://github.com/DonnC/pywce/blob/master/example/standalone_chatbot/main.py)_

- **Send messages** (text, media, templates, interactive)
- **Receive and process webhooks**
- **Media management** (upload and download)
- **Out of the box utilities** using the `WhatsApp.Utils` class.

Example usage:

```python
from pywce import WhatsAppConfig, WhatsApp

config = WhatsAppConfig(
    token="your_access_token",
    phone_number_id="your_phone_number_id",
    hub_verification_token="your_webhook_hub_verification_token"
)

whatsapp = WhatsApp(whatsapp_config=config)

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

### Template Engine ChatBot

Here's a simple example template to get you started:

_**Note:** Checkout complete example chatbot with [Fast Api here](https://github.com/DonnC/pywce/blob/master/example/engine_chatbot/main.py)_

1. Define your YAML template:

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
```

2. Write your hook:

```python
# example/hooks/name_template.py
from pywce import hook, HookArg, TemplateDynamicBody

@hook
def username(arg: HookArg) -> HookArg:
    # set render payload data to match the required template dynamic var
    arg.template_body = TemplateDynamicBody(
        render_template_payload={"name": arg.user.name}
    )

    return arg
```

3. Start the engine:

```python
from pywce import PywceEngine, PywceEngineConfig

config = PywceEngineConfig(
    templates_dir="path/to/templates",
    start_template_stage="START-MENU"
)
engine = PywceEngine(config=config)
```

## Documentation

Visit the [official documentation](https://docs.page/donnc/wce) for a detailed guide.

## Contributing

We welcome contributions! Please check out the [Contributing Guide](https://github.com/DonnC/pywce/blob/master/CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/DonnC/pywce/blob/master/LICENCE) file for details.
