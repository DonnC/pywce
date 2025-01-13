# PyWCE - Python WhatsApp Cloud Engine

A package for creating WhatsApp chatbots using a template-driven approach. It decouples 
the engine from the WhatsApp client library, allowing developers to use them independently or 
together. 

Templates use YAML allowing you to define conversation flows and business logic in a clean and modular
way.

## Features

- **Template-Driven Design**: Use YAML templates for conversational flows.
- **Hooks for Business Logic**: Attach Python functions to process messages or actions.
- Easy-to-use API for WhatsApp Cloud.
- Supports dynamic messages with placeholders.
- Built-in support for WhatsApp Webhooks.

### WhatsApp Client Library

PyWCE provides a simple, Pythonic interface to interact with the WhatsApp Cloud API:

_**Note**: You can use pywce as a standalone whatsapp client library_

_Checkout complete standalone chatbot with [Fast Api here](/example/standalone_chatbot/main.py)_

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
    hub_verification_token="your_hub_verification_token"
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

## Installation

Install PyWCE using pip:

```bash
pip install pywce
```

## Quick Start

Here's a simple example template to get you started:

_**Note:** Checkout complete example chatbot with [Fast Api here](/example/engine_chatbot/main.py)_

1. Define your YAML template:

```yaml
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
from pywce import HookArg, TemplateDynamicBody


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

## Setting up

To get started using this package, you will need **TOKEN** and **TEST WHATSAPP NUMBER** (the library works either with a
production phone number, if you have one) which you can get from
the [Facebook Developer Portal](https://developers.facebook.com/)

Here are steps to follow for you to get started:

1. [Go to your apps](https://developers.facebook.com/apps)
2. [create an app](https://developers.facebook.com/apps/create/)
3. Select Business >> Business
4. It will prompt you to enter basic app informations
5. It will ask you to add products to your app
   a. Add WhatsApp Messenger
6. Right there you will see a your **TOKEN** and **TEST WHATSAPP NUMBER** and its phone_number_id
7. Lastly verify the number you will be using for testing on the **To** field.

Once you've followed the above procedures you're ready to start your bot development journey.


## Documentation

Visit the [official documentation](https://docs.page/donnc/wce) for a detailed guide.

## Contributing

We welcome contributions! Please check out the [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
