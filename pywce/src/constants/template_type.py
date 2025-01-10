from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateTypeConstants:
    BUTTON = "button"
    LIST = "list"
    TEXT = "text"
    DYNAMIC = "dynamic"
    MEDIA = "media"
    FLOW = "flow"
    LOCATION = "location"
    REQUEST_LOCATION = "request-location"


TEMPLATE_TYPE_MAPPING = {
    "button": TemplateTypeConstants.BUTTON,
    "list": TemplateTypeConstants.LIST,
    "text": TemplateTypeConstants.TEXT,
    "dynamic": TemplateTypeConstants.DYNAMIC,
    "media": TemplateTypeConstants.MEDIA,
    "flow": TemplateTypeConstants.FLOW,
    "location": TemplateTypeConstants.LOCATION,
    "request-location": TemplateTypeConstants.REQUEST_LOCATION,
}
