from dataclasses import dataclass


@dataclass(frozen=True)
class EngineConstants:
    MESSAGE_QUEUE_COUNT: int = 10
    TIMEOUT_REQUEST_RETRY_COUNT = 2
    REGEX_PLACEHOLDER = "re:"
    REST_HOOK_PLACEHOLDER = "rest:"
    TRIGGER_ROUTE_PARAM = "trigger-route"
    RETRY_NAME_KEY = "Retry"
    DYNAMIC_ROUTE_KEY = "route"
    DYNAMIC_BODY_STAGE = "DYNAMIC_BODY_STAGE"
    DYNAMIC_LAST_TEMPLATE = "DTPL_LAST_STAGE"
