from dataclasses import dataclass


@dataclass(frozen=True)
class EngineConstants:
    MESSAGE_QUEUE_COUNT: int = 10
    REGEX_PLACEHOLDER = "re:"
    DYNAMIC_BODY_STAGE = "DYNAMIC_BODY_STAGE"
    TIMEOUT_REQUEST_RETRY_COUNT = 2
    RETRY_NAME_KEY = "Retry"
    DYNAMIC_LAST_TEMPLATE = "DTPL_LAST_STAGE"