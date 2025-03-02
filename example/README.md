# Examples
A curated list of example chatbots developed using the pywce library.

> [!NOTE]
> The example projects uses [Fast Api](https://fastapi.tiangolo.com/)


## Running
Install project dependencies
```bash

pip install -r requirements.txt
```

## Setup
The examples have all have the same structure in [common directory](common)

To run the bots, each example should have its own `.env` file (view the example [.env.example](.env.example) file)

## ChatBots
### Demos
Check out demo videos in [demo folder](videos)

### [Nikk's Car Rental ChatBot](car_rental)

<video src="demo/rental.mp4" width="320" height="240" controls></video>

A car rental chatbot using WhatsApp Flows and showcasing the powerful features of pywce. 

> [!NOTE]
> For the purpose of demo, some implementation have been mocked 

Features
1. Rent a car
2. Get a quotation
3. Pay for car rental

_and more_


You can find the conversation flow in [templates dir](car_rental/templates)

### [AI FAQ, Car rental ChatBot](ai_agents)
A template-driven chatbot with AI agent invocation. User can invoke AI agent to chat with by invoking it.

The engine will be aware of AI session and auto-template session.

> [!NOTE]
> Experience with & having OpenAI keys required

This example is built on top of Nikk's Car Rental ChatBot

Features
1. Rent a car
2. Chat with AI agent

_and more_


### [eHailing ChatBot](ehailing)

<video src="demo/ehailing.mp4" width="320" height="240" controls></video>

An e-hailing **PickDrive** conceptual whatsapp chatbot for _(inspired by **InDrive**)_.
You can find the conversation flow in [templates dir](ehailing/templates/ehailing.yaml)

### [Standalone ChatBot](chatbot)
An example chatbot using pywce as yet another WhatsApp Client library.

This is for developers who have no need for pywce core engine but want to process their own business handling logic

## Support
Thank you, if you like or find my work helpful to you.
Your support goes a long way in taking this work further, be it sharing with your network, staring the repository, contributing or even financial support - I appreciate any form of support.

or get in touch with me on [donychinhuru@gmail.com](mailto:donychinhuru@gmail.com)

Want a chatbot developed for you or just to say hi or get in touch on software development projects or consultancy? You can contact me on the email above.