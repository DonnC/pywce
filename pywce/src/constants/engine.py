from dataclasses import dataclass


@dataclass(frozen=True)
class EngineConstants:
    MESSAGE_QUEUE_COUNT: int = 20
    TIMEOUT_REQUEST_RETRY_COUNT = 2
    REGEX_PLACEHOLDER = "re:"
    EXT_HOOK_PROCESSOR_PLACEHOLDER = "ext:"
    TRIGGER_ROUTE_PARAM = "trigger-route"

    # TRIGGER-NEXT-STAGE | TRIGGER-INNER-ROUTE
    TRIGGER_ROUTE_SEPARATOR = "|"

    # holds a list of WhatsApp templates components
    # {WHATSAPP_TEMPLATE_KEY: [..components list..]}
    WHATSAPP_TEMPLATE_KEY = "templates"

    DYNAMIC_BODY_STAGE = "DTPL_BODY_STAGE"
    DYNAMIC_LAST_TEMPLATE = "DTPL_LAST_STAGE"

    # default buttons
    DEFAULT_MENU_BTN_NAME = "Menu"
    DEFAULT_RETRY_BTN_NAME = "Retry"
    DEFAULT_REPORT_BTN_NAME = "Report"
    DEFAULT_BACK_BTN_NAME = "Back"

    GLOBAL_BUILTIN_TRIGGERS_LC = [DEFAULT_BACK_BTN_NAME.lower(), DEFAULT_MENU_BTN_NAME.lower(), DEFAULT_RETRY_BTN_NAME.lower(), DEFAULT_REPORT_BTN_NAME.lower()]