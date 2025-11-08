import json
from typing import Dict, List, Any


class VisualTranslator:
    """
    Translates a Visual Builder JSON export into the pywce-compatible 
    dictionary format. This class is stateless.
    """

    def translate(self, builder_json: str) -> Dict[str, Any]:
        """
        Main entry point for translation.

        Args:
            builder_json: A string containing the JSON from 
                             the Visual Builder builder.

        Returns:
            A dictionary in pywce format, e.g., {"START MENU": {...}}
        """
        try:
            data = json.loads(builder_json)
            templates_list = data.get("templates", [])
            if not templates_list:
                return {}

            # --- Pass 1: Create ID-to-Name map ---
            id_to_name_map = {
                tpl.get("id"): tpl.get("name")
                for tpl in templates_list
                if tpl.get("id") and tpl.get("name")
            }

            # --- Pass 2: Transform and build the dict ---
            engine_flow = {}
            for tpl in templates_list:
                template_name = tpl.get("name")
                if not template_name:
                    continue

                transformed_tpl = self._transform_template(tpl, id_to_name_map)
                engine_flow[template_name] = transformed_tpl

            return engine_flow

        except Exception as e:
            # Handle JSON parsing errors, etc.
            print(f"Visual Builder Translation Error: {e}")
            return {}

    def _transform_template(self, tpl: Dict, id_map: Dict) -> Dict:
        """Transforms a single node from Visual Builder."""

        kind = tpl.get("type")
        message = tpl.get("message", {})

        # Fix schema mismatches (e.g., for list sections)
        if kind == "list" and "sections" in message:
            message["sections"] = self._transform_list_sections(message["sections"])

        transformed_tpl = {
            "kind": kind,
            "message": message,
        }

        # Transform routes
        transformed_routes = {}
        for route in tpl.get("routes", []):
            pattern = route.get("pattern", "")
            target_id = route.get("connectedTo")
            if target_id and target_id in id_map:
                target_name = id_map[target_id]
                transformed_routes[pattern] = target_name

        transformed_tpl["routes"] = transformed_routes

        # Flatten 'settings'
        if "settings" in tpl:
            transformed_tpl.update(tpl["settings"])
            # TODO: fix message-id

        # Flatten 'hooks'
        if "hooks" in tpl:
            for hook in tpl["hooks"]:
                transformed_tpl[hook.get("type")] = hook.get("path")
                # TODO: fix params

        return transformed_tpl

    def _transform_list_sections(self, sections: List[Dict]) -> List[Dict]:
        """Transforms list rows to match SectionRowItem Pydantic model."""
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
