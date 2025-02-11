# Examples
A example chatbots using pywce library

The example projects uses [Fast Api](https://fastapi.tiangolo.com/)

## Running
Install project dependencies
```bash
pip install -r requirements.txt
```

## Structure
This folder contains 2 folders

### [eHailing ChatBot](ehailing)
An example chatbot using pywce core engine.

An e-hailing **PickDrive** conceptual whatsapp chatbot for _(inspired by **InDrive**)_.
You can find the conversation flow in [templates dir](ehailing/templates/ehailing.yaml)

### [Standalone ChatBot](chatbot)
An example chatbot using pywce as yet another WhatsApp Client library.

This is for developers who have no need for pywce core engine but want to process their own business handling logic
