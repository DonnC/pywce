# https://github.com/panda-zw/fastapi-whatsapp-openai/blob/main/services/openai.py
import asyncio
import os
import shelve
import time
from typing import Optional, Union, Dict, List, Literal, Callable

from dotenv import load_dotenv
from pydantic import BaseModel

from pywce.src.utils import pywce_logger

try:
    import openai
    from openai import OpenAI, APIConnectionError
    from openai.types.beta import Assistant
    import docstring_parser
except ImportError:
    openai = None
    docstring_parser = None

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

_logger = pywce_logger(__name__)


class AiResponse(BaseModel):
    typ: Literal["text", "button", "list"]
    message: str
    title: Optional[str]
    options: List[Union[str, Dict]]


class AiService:
    """
        Create general AI ext handler prompt

        instructions:
        1. you are a customer support ai agent for a local bank. The bank has omnichannel digital platforms for its clients.
        2.



    """
    _history_folder = "ai_history"
    _threads_db: str = "ai_threads_db"

    _tool_belt: Dict[str, Callable]

    _prompt: str = """WhatsApp supports different message types, including `text`, `button`, and `list`.

        When generating responses, consider the following message type limitations:  
        - **`text`**: A text message best for open-ended responses. The message body supports up to 4096 characters.
        - **`button`**: Up to 3 options, each ≤ 20 characters (exact limit: 3 buttons max). Suitable for short choices like 'Check Balance' or 'Contact Support.'
            A button must have a single `title`: A short label describing the list (≤ 60 chars) — used as the button header.  
        - **`list`**: Up to **10 options**, each with:  
          - `id`: Max **200 characters** (required, unique identifier)  
          - `description`: Max **72 characters** (always include when possible for clarity; omit only if not applicable). 
          - A single `title`: A short label describing the list (≤ 60 chars) — used as the list header.
        
        **Message Type Rules:**  
        - Use **`text`** for short, direct answers with no selections.  
        - Use **`button`** if there are up to **3** short options.  
        - Use **`list`** if there are up to **10** more detailed options.  
        
        If a response exceeds character limits for button or list, automatically shorten the text. If shortening isn’t possible, fallback to text
        
        - For a single option, use button or text (choose the most natural fit).
        - If a list requires more than 10 options, truncate the list or fallback to text with the most relevant options.
        
        **For `list` type**, only return: 
        - **`title`**: A short label describing the list (≤ 60 chars).  
        - A list of dict selectable options each with: 
            - **`id`**: A short, clear identifier (≤ 200 chars).  
            - **`description`**: A concise description (≤ 72 chars).  
            
        **For `button` type**, only return: 
        - **`title`**: A short label describing the message (≤ 60 chars).  
        - A list of string selectable options to use as buttons (≤ 20 chars)
        
        Generate and return a structured JSON response object like this:
        {
          "typ": "<message_type>",
          "message": "<your_response_text>",
          "title": "<your_response_title>", # Only include if type is  `button` or `list`
          "options": []  # Only include if type is `button` or `list`
        }
        
        ### Example responses
        Example 1:
        User: What services do you offer?
        AI Response:
        ```json
        {
          "typ": "list",
          "message": "Select a shipping option:",
          "title": "Shipping Options",
          "options": [
            {"id": "priority_express", "description": "Next Day to 2 Days"},
            {"id": "priority_mail", "description": "1–3 Days"},
            {"id": "ground_advantage", "description": "2–5 Days"},
            {"id": "media_mail", "description": "2–8 Days"}
          ]
        }
        ```
        
        Example 2:
        User: Can you help me book a car?
        AI Response:
        ```json
        {
          "typ": "button",
          "message": "Would you like to proceed with booking?",
          "title": "Car Booking",
          "options": ["Yes", "No"]
        }
        ```
        
        Example 3:
        User: Tell me Zimbabwean history
        AI Response:
        ```json
        {
          "typ": "text",
          "message": "Zimbabwe got its independence in 1980. It went through a series of economic changes since 2000. Would you like to know more?"
        }
        ```
        """

    def __init__(self, agent_name: str, instructions: str, api_key: str, model: str):
        self._verify_dependencies()

        self.client = OpenAI(api_key=api_key)
        self.name = agent_name
        self.model = model
        self.instructions = f"{instructions}\n\n{self._prompt}"
        self.assistant_files: List[str] = []
        self.tools: Union[List[Dict], None] = None

        self.assistant = self.create_assistant()

    def _verify_dependencies(self):
        if openai is None or docstring_parser is None:
            raise RuntimeError(
                "AI functionality requires additional dependencies. Install using `pip install pywce[ai]`.")

    def _get_tools_in_open_ai_format(self):
        python_type_to_json_type = {
            "str": "string",
            "int": "number",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object"
        }

        return [
            {
                "type": "function",
                "function": {
                    "name": tool.__name__,
                    "description": docstring_parser.parse(tool.__doc__).short_description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            p.arg_name: {
                                "type": python_type_to_json_type.get(p.type_name, "string"),
                                "description": p.description
                            }
                            for p in docstring_parser.parse(tool.__doc__).params

                        },
                        "required": [
                            p.arg_name
                            for p in docstring_parser.parse(tool.__doc__).params
                            if not p.is_optional
                        ]
                    }
                }
            }
            for tool in self._tool_belt.values()
        ]

    def _clean_agent_name(self):
        clean_name = self.name.strip().replace("-", "_").replace(" ", "_")
        return clean_name

    def _create_thread_db_id(self, wa_id):
        return f"{wa_id}_{self._clean_agent_name()}"

    def add_file(self, file_path: str, purpose: str = 'assistants'):
        """Uploads a file and stores its ID for assistant use."""
        with open(file_path, 'rb') as file:
            response = self.client.files.create(file=file, purpose=purpose)
            self.assistant_files.append(response.id)

    def register_tool(self, tool_name: str, tool_function: Dict):
        """Registers a tool by name and function."""
        self.tools.append({'name': tool_name, 'function': tool_function})

    def create_assistant(self) -> Assistant:
        _logger.info("Creating assistant..")
        assistant = self.client.beta.assistants.create(
            model=self.model,
            name=self.name,
            instructions=self.instructions,
            tools=self.tools or [{"type": "retrieval"}]
        )

        return assistant

    async def _store_thread(self, wa_id, thread_id):
        with shelve.open(self._threads_db, writeback=True) as threads_shelf:
            threads_shelf[self._create_thread_db_id(wa_id)] = thread_id

    async def _check_if_thread_exists(self, wa_id):
        with shelve.open(self._threads_db, writeback=True) as threads_shelf:
            return threads_shelf.get(self._create_thread_db_id(wa_id), None)

    async def _wait_for_run_completion(self, thread):
        """
        Wait for any active run associated with the thread to complete.
        """
        timeout_in_seconds = 60
        start_time = time.time()

        while True:
            run_list = self.client.beta.threads.runs.list(thread_id=thread.id)
            active_runs = [run for run in run_list.data if run.status in ["queued", "in_progress"]]

            if not active_runs:
                break

            if time.time() - start_time > timeout_in_seconds:
                raise TimeoutError("Waiting for run to complete timed out")

            await asyncio.sleep(1)

    async def run_assistant(self, thread):
        try:
            _logger.debug("Running assistant: %s", self.assistant)
            assistant = self.client.beta.assistants.retrieve(self.assistant.id)
            _logger.debug("Assistant retrieved")

            # Wait for any active run to complete
            await self._wait_for_run_completion(thread)

            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id,
                response_format=AiResponse
                # tool_resources=self.assistant_files
            )

            _logger.debug(f"Initial run status: {run.status}")

            timeout_in_seconds = 60
            start_time = time.time()

            while run.status != "completed":
                if time.time() - start_time > timeout_in_seconds:
                    raise TimeoutError("Assistant run timed out")

                await asyncio.sleep(0.5)
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                _logger.debug(f"Run status: {run.status}")

            if run.status == "failed":
                raise RuntimeError("Assistant run failed")

            messages = self.client.beta.threads.messages.list(thread_id=thread.id)

            _logger.debug("Messages retrieved: %s", messages.data[0].content[0])

            new_message = messages.data[0].content[0].text.value
            _logger.info(f"Generated message: {new_message}")
            return new_message

        except APIConnectionError as e:
            _logger.error(f"API Connection Error: {e}")
            raise e
        except Exception as e:
            _logger.error(f"An unexpected error occurred: {e}")
            raise e

    async def generate_response(self, message: str, wa_id: str):
        _logger.info("Generating response..")
        thread_id = await self._check_if_thread_exists(wa_id)

        if thread_id is None:
            _logger.info(f"Creating new thread for agent: {self.name} with user: {wa_id}")
            thread = self.client.beta.threads.create()
            await self._store_thread(wa_id, thread.id)
            thread_id = thread.id
        else:
            _logger.info(f"Retrieving existing thread for agent: {self.name} with user: {wa_id}")
            thread = self.client.beta.threads.retrieve(thread_id)

        # Ensure no active runs before adding a new message
        await self._wait_for_run_completion(thread)

        message_response = self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        _logger.debug("AI message response: %s", message_response.content)

        new_message = await self.run_assistant(thread)

        return new_message
