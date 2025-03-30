# https://github.com/panda-zw/fastapi-whatsapp-openai/blob/main/services/openai.py
# https://github.com/jeanmaried/openai-assistant-blog/blob/main/agent.py


import json
import os
import shelve
import time
from typing import Optional, Union, Dict, List, Literal, Callable

from dotenv import load_dotenv
from pydantic import BaseModel

from pywce.src.exceptions import AiException
from pywce.src.utils.engine_logger import pywce_logger

try:
    import openai
    from openai import OpenAI, APIConnectionError
    import docstring_parser
except ImportError:
    openai = None
    docstring_parser = None

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
BASE_URL = os.getenv("OPENAI_BASE_URL", None)
RUN_TIMEOUT_IN_SECONDS = int(os.getenv("OPENAI_RUN_TIMEOUT_IN_SECONDS", "120"))

_logger = pywce_logger(__name__)


class AiResponse(BaseModel):
    typ: Literal["text", "button", "list"]
    message: str
    title: Optional[str] = None
    options: Optional[List[Union[str, Dict]]] = None


class AiService:
    """
        Create general AI ext handler prompt

        instructions:
        1. you are a customer support ai agent for a local bank. The bank has omnichannel digital platforms for its clients.

        Gemini baseUrl: "https://generativelanguage.googleapis.com/v1beta/"
    """
    _history_folder = "ai_history"
    _threads_db: str = "ai_threads_db"

    _prompt: str = """WhatsApp supports different message types, including `text`, `button`, and `list`.

        When generating responses, consider the following message type limitations:  
        - **`text`**: A text message best for open-ended responses. The message body supports up to 4096 characters.
        - **`button`**: Up to 3 options, each ≤ 20 characters (exact limit: 3 buttons max). Suitable for short choices like 'Check Balance' or 'Contact Support.'
            - A button must have a single `title`: A short label describing the list (≤ 60 chars) — used as the button header.  
            - Each option must adhere to char limit minimum 1 upto 20 characters.
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

    def __init__(self, agent_name: str, instructions: str, tools: Dict[str, Callable]):
        self._verify_dependencies()

        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=BASE_URL)
        self.name = agent_name
        self.instructions = f"{instructions}\n\n{self._prompt}"
        self.assistant_files: List[str] = []
        self.tool_belt = tools

        self.assistant = self.get_assistant()

    def _verify_dependencies(self):
        if openai is None or docstring_parser is None:
            raise AiException(
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
            for tool in self.tool_belt.values()
        ]

    def _clean_agent_name(self):
        clean_name = self.name.strip().replace("-", "_").replace(" ", "_")
        return clean_name

    def _create_thread_db_id(self, wa_id):
        return f"{wa_id}_{self._clean_agent_name()}"

    def add_file(self, file_path: str):
        """Uploads a file and stores its ID for assistant use."""
        with open(file_path, 'rb') as file:
            response = self.client.files.create(file=file, purpose='assistants')
            _logger.debug("Added assistant file with id: %s", response.id)
            self.assistant_files.append(response.id)

    def get_assistant(self):
        assistants = self.client.beta.assistants.list()

        for assistant in assistants.data:
            if assistant.name == self.name:
                _logger.info("Assistant already exists.")
                return assistant

        _logger.info("No assistant found, creating..")

        assistant = self.client.beta.assistants.create(
            model=OPENAI_MODEL,
            # response_format=AiResponse,
            name=self.name)

        _logger.info("New assistant created!")
        return assistant

    def _store_thread(self, wa_id, thread_id):
        with shelve.open(self._threads_db, writeback=True) as threads_shelf:
            threads_shelf[self._create_thread_db_id(wa_id)] = thread_id

    def _check_if_thread_exists(self, wa_id):
        with shelve.open(self._threads_db, writeback=True) as threads_shelf:
            return threads_shelf.get(self._create_thread_db_id(wa_id), None)

    def _wait_for_run_completion(self, thread):
        """
        Wait for any active run associated with the thread to complete.
        """
        start_time = time.time()

        while True:
            run_list = self.client.beta.threads.runs.list(thread_id=thread.id)
            active_runs = [run for run in run_list.data if run.status in ["queued", "in_progress"]]

            if not active_runs:
                break

            elapsed_time = time.time() - start_time
            if elapsed_time > RUN_TIMEOUT_IN_SECONDS:
                raise AiException("Waiting for run to complete timed out")

            time.sleep(1)

    def _cancel_run(self, run_id, thread_id):
        self.client.beta.threads.runs.cancel(
            run_id=run_id,
            thread_id=thread_id
        )

    def _get_thread(self, wa_id: str):
        thread_id = self._check_if_thread_exists(wa_id)

        if thread_id is None:
            _logger.info(f"Creating new thread for agent: {self.name} with user: {wa_id}")
            thread = self.client.beta.threads.create()
            self._store_thread(wa_id, thread.id)
        else:
            thread = self.client.beta.threads.retrieve(thread_id)

        return thread

    def _create_run(self, thread_id):
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id,
            instructions=self.instructions,
            # response_format=AiResponse,
            tools=self._get_tools_in_open_ai_format() or None
        )

        return run

    def _retrieve_run(self, run_id, thread_id):
        return self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

    def _run_assistant(self, thread, run):
        try:
            self._wait_for_run_completion(thread)

            status = run.status

            start_time = time.time()

            _logger.debug("Starting poll run..")

            while status != "completed":
                if status == 'failed':
                    raise AiException(f"Run failed with error: {run.last_error}")

                if status == 'expired':
                    raise AiException("Run expired")

                if status == 'requires_action':
                    self._call_tools(run.id, thread.id, run.required_action.submit_tool_outputs.tool_calls)

                time.sleep(2)

                run = self._retrieve_run(run.id, thread.id)
                status = run.status

                elapsed_time = time.time() - start_time
                if elapsed_time > RUN_TIMEOUT_IN_SECONDS:
                    self._cancel_run(run.id, thread.id)
                    raise AiException("Assistant run timed out")

        except APIConnectionError as e:
            _logger.error(f"API Connection Error: {e}")
            raise e
        except Exception as e:
            _logger.error(f"An unexpected error occurred: {e}")
            raise e

    def _call_tools(self, run_id, thread_id, tool_calls: list[dict]):
        _logger.debug("Calling %d found tools, thread id: %s", len(tool_calls), thread_id)

        tool_outputs = []

        for tool_call in tool_calls:
            function = tool_call.function
            function_args = json.loads(function.arguments)
            function_to_call = self.tool_belt[function.name]
            function_response = function_to_call(**function_args)
            tool_outputs.append({"tool_call_id": tool_call.id, "output": function_response})

        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )

    def _add_message(self, thread_id, message: str):
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

    def _get_last_message(self, thread_id):
        content = self.client.beta.threads.messages.list(
            thread_id=thread_id,
        ).data[0].content[0]

        return content.text.value

    def _parse_response(self, yaml_text_response: str) -> AiResponse:
        """
        _parse_response(yaml_text_response)

        Args:
            _parse_response (str): ai generated response as yaml json

        Returns:
            AiResponse: the parse ai response as an object
        """

        json_data = yaml_text_response.strip("```json\n").strip("```")
        return AiResponse(**json.loads(json_data))

    def generate_response(self, message: str, wa_id: str) -> AiResponse:
        assert len(message) > 0, "Message must not be empty"

        _logger.debug("Generating AI agent response..")

        thread = self._get_thread(wa_id)

        self._wait_for_run_completion(thread)

        self._add_message(thread.id, message)

        run = self._create_run(thread.id)

        self._run_assistant(thread, run)

        agent_response = self._get_last_message(thread.id)

        _logger.info(f"Raw agent response: {agent_response}")

        return self._parse_response(agent_response)
