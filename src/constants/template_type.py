from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateKeyConstants:
    BUTTON = "button"
    LIST = "list"
    TEXT = "text"
    DYNAMIC = "dynamic"
    MEDIA = "media"
    REQUEST_LOCATION = "request-location"
