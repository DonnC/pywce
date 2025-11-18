import json
import logging
from typing import Dict, List, Any, Tuple, Optional

from pywce.src.constants.engine import EngineConstants
from pywce.src.templates import EngineRoute


_logger = logging.getLogger(__name__)

class VisualTranslator:
    """
    Translates a React Flow JSON export into the pywce-compatible
    dictionary format and a list of triggers.

    This class is stateless and part of your core pywce library.
    ---

    """

    START_MENU: Optional[str] = None
    REPORT_MENU: Optional[str] = None

    def __init__(self):
        pass

    def translate(self, react_flow_json: str) -> Tuple[Dict[str, Any], List[EngineRoute]]:
        """
        Main entry point for translation.

        Args:
            react_flow_json: A string containing the JSON from
                             the React Flow builder.

        Returns:
            A tuple containing:
            1. (Dict[str, Any]): The pywce-compatible templates dictionary.
            2. (List[EngineRoute]): A list of global triggers.
        """
        pywce_flow: Dict[str, Any] = {}
        pywce_triggers: List[EngineRoute] = []

        try:
            data = json.loads(react_flow_json)
            templates_list: List[Dict] = data.get("templates", [])
            if not templates_list:
                return ({}, [])

            # --- Pass 1: Create ID-to-Name map ---
            id_to_name_map = {
                tpl.get("id"): tpl.get("name")
                for tpl in templates_list
                if tpl.get("id") and tpl.get("name")
            }

            # --- Pass 2: Transform templates and extract triggers ---
            for tpl in templates_list:
                template_name = tpl.get("name")
                if not template_name:
                    continue

                # 1. Transform the template node
                transformed_tpl = self._transform_template(tpl, id_to_name_map)
                pywce_flow[template_name] = transformed_tpl

                settings = tpl.get("settings", {})

                if settings.get("isReport", False):
                    self.REPORT_MENU = template_name

                if settings.get("isStart", False):
                    self.START_MENU = template_name

                # 2. Extract global triggers
                trigger_pattern = settings.get("trigger")

                if trigger_pattern:
                    #
                    if not trigger_pattern.startswith(EngineConstants.REGEX_PLACEHOLDER):
                        trigger_input = f"{EngineConstants.REGEX_PLACEHOLDER}{trigger_pattern}"
                    else:
                        trigger_input = trigger_pattern

                    pywce_triggers.append(EngineRoute(
                        user_input=trigger_input,
                        next_stage=template_name,
                        is_regex=str(trigger_input).startswith(EngineConstants.REGEX_PLACEHOLDER)
                    ))

            return (pywce_flow, pywce_triggers)

        except:
            _logger.error("Builder translation error", exc_info=True)
            return ({}, [])

    def _transform_template(self, tpl: Dict, id_map: Dict) -> Dict:
        """Transforms a single node from Builder into a pywce-compatible dict."""

        kind = tpl.get("type")
        message = tpl.get("message", {})

        # Fix schema mismatches (e.g., for list sections)
        if kind == "list" and "sections" in message:
            message["sections"] = self._transform_list_sections(message["sections"])

        transformed_tpl = {
            "kind": kind,
            "message": message,
        }

        # --- Transform Routes ---
        # Converts the list of route objects into the {pattern: next_stage} dict
        transformed_routes = {}
        for route in tpl.get("routes", []):
            pattern = route.get("pattern")
            target_id = route.get("connectedTo")
            is_regex = route.get("isRegex", False)

            # Determine the final key for the routes dict
            final_pattern_key = str(pattern)  # Ensure it's a string

            if is_regex and not final_pattern_key.startswith(EngineConstants.REGEX_PLACEHOLDER):
                final_pattern_key = f"{EngineConstants.REGEX_PLACEHOLDER}{final_pattern_key}"

            target_name = id_map.get(target_id)
            if target_name:  # Only add routes that connect to another node
                transformed_routes[final_pattern_key] = target_name

        transformed_tpl["routes"] = transformed_routes

        # --- Flatten Settings ---
        # Maps keys from 'settings' to the BaseTemplate model fields
        settings = tpl.get("settings", {})
        if settings:
            # Direct 1:1 maps
            for key in ["checkpoint", "react", "prop", "params", "typing", "authenticated", "session", "transient"]:
                if key in settings:
                    transformed_tpl[key] = settings[key]

            # Renamed maps (JSON key -> Pydantic field name)
            if "ack" in settings:
                transformed_tpl["acknowledge"] = settings["ack"]
            if "replyMsgId" in settings:
                transformed_tpl["reply_message_id"] = settings["replyMsgId"]

        # --- Flatten Hooks ---
        # Maps the list of hook objects to the BaseTemplate model fields
        hooks = tpl.get("hooks", [])
        for hook in hooks:
            hook_type = hook.get("type")
            hook_path = hook.get("path")

            # Map from JSON 'type' to Pydantic 'field name'
            if hook_type and hook_path:
                if hook_type == "on-receive":
                    transformed_tpl["on_receive"] = hook_path
                elif hook_type == "on-generate":
                    transformed_tpl["on_generate"] = hook_path
                elif hook_type == "template":
                    transformed_tpl["template"] = hook_path
                elif hook_type == "router":
                    transformed_tpl["router"] = hook_path
                elif hook_type == "middleware":
                    transformed_tpl["middleware"] = hook_path

        return transformed_tpl

    def _transform_list_sections(self, sections: List[Dict]) -> List[Dict]:
        """
        Transforms list rows to match SectionRowItem Pydantic model.
        - Renames 'id' to 'identifier'
        - Renames 'desc' to 'description'
        """
        transformed_sections = []
        for section in sections:
            transformed_rows = []
            for row in section.get("rows", []):
                transformed_row = row.copy()
                if "id" in transformed_row:
                    transformed_row["identifier"] = transformed_row.pop("id")
                if "desc" in transformed_row:
                    transformed_row["description"] = transformed_row.pop("desc")
                transformed_rows.append(transformed_row)

            section["rows"] = transformed_rows
            transformed_sections.append(section)
        return transformed_sections
