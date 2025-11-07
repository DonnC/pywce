from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateTypeConstants:
    BUTTON = "button"
    CTA = "cta"
    LIST = "list"
    TEXT = "text"
    TEMPLATE = "templates"
    DYNAMIC = "dynamic"
    MEDIA = "media"
    FLOW = "flow"
    LOCATION = "location"
    REQUEST_LOCATION = "request-location"

    # catalog / products
    CATALOG = "catalog"
    SINGLE_PRODUCT = "product"
    MULTI_PRODUCT = "products"


TEMPLATE_TYPE_MAPPING = {
    "button": TemplateTypeConstants.BUTTON,
    "cta": TemplateTypeConstants.CTA,
    "catalog": TemplateTypeConstants.CATALOG,
    "product": TemplateTypeConstants.SINGLE_PRODUCT,
    "products": TemplateTypeConstants.MULTI_PRODUCT,
    "templates": TemplateTypeConstants.TEMPLATE,
    "list": TemplateTypeConstants.LIST,
    "text": TemplateTypeConstants.TEXT,
    "dynamic": TemplateTypeConstants.DYNAMIC,
    "media": TemplateTypeConstants.MEDIA,
    "flow": TemplateTypeConstants.FLOW,
    "location": TemplateTypeConstants.LOCATION,
    "request-location": TemplateTypeConstants.REQUEST_LOCATION,
}
