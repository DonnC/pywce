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

### [Engine ChatBot](engine_chatbot)
An example chatbot using pywce core engine.

A template-driven PickDrive conceptual whatsapp chatbot for InDrive.
You can find the conversation flow in [templates dir](engine_chatbot/templates/ehailing-bot.yaml)

### [Standalone ChatBot](standalone_chatbot)
An example chatbot using core pywce whatsapp client **without** using the core template-driven engine.

This is for DIY developers who just want to use yet another WhatsApp python library and handle their own logic
