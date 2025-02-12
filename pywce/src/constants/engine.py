from dataclasses import dataclass


@dataclass(frozen=True)
class EngineConstants:
    MESSAGE_QUEUE_COUNT: int = 100
    TIMEOUT_REQUEST_RETRY_COUNT = 2
    REGEX_PLACEHOLDER = "re:"
    TRIGGER_ROUTE_PARAM = "trigger-route"

    RETRY_NAME_KEY = "Retry"

    # holds a list of WhatsApp template components
    # {WHATSAPP_TEMPLATE_KEY: [..components list..]}
    WHATSAPP_TEMPLATE_KEY = "template"
    DYNAMIC_ROUTE_KEY = "route"

    DYNAMIC_BODY_STAGE = "DTPL_BODY_STAGE"
    DYNAMIC_LAST_TEMPLATE = "DTPL_LAST_STAGE"

    # default buttons
    DEFAULT_MENU_BTN_NAME = "Menu"
    DEFAULT_RETRY_BTN_NAME = "Retry"
    DEFAULT_REPORT_BTN_NAME = "Report"
