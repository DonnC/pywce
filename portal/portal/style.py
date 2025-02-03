from typing import Dict


class Style:
    admin: Dict[str, str] = {
        "padding": "1em",
        "border_radius": "5px",
        "margin_y": "0.5em",
        "margin_left": "20%",
        "background_color": "rgb(59, 130, 246)",
        "color": "white",
        "max_width": "30em",
        "display": "inline-block",
    }

    user: Dict[str, str] = {
        "padding": "1em",
        "border_radius": "5px",
        "margin_y": "0.5em",
        "margin_right": "20%",
        "background_color": "rgb(229, 231, 235)",
        "max_width": "30em",
        "display": "inline-block",
    }
