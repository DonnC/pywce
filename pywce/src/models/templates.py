from typing import Union, Literal, Annotated

from pywce.src.models.base_model import BaseTemplate
from pywce.src.models.messages import *


# message: str only     =======================================
class TextTemplate(BaseTemplate):
    typ: Literal["text"] = "text"
    message: str


class DynamicTemplate(BaseTemplate):
    typ: Literal["dynamic"] = "dynamic"
    message: str


class RequestLocationTemplate(BaseTemplate):
    typ: Literal["request-location"] = "request-location"
    message: str


# ============================================================

class ButtonTemplate(BaseTemplate):
    typ: Literal["button"] = "button"
    message: ButtonMessage


class CtaTemplate(BaseTemplate):
    typ: Literal["cta"] = "cta"
    message: CTAMessage


class ListTemplate(BaseTemplate):
    typ: Literal["list"] = "list"
    message: ListMessage


class TemplateTemplate(BaseTemplate):
    typ: Literal["template"] = "template"
    message: TemplateMessage


class MediaTemplate(BaseTemplate):
    typ: Literal["media"] = "media"
    message: MediaMessage


class FlowTemplate(BaseTemplate):
    typ: Literal["flow"] = "flow"
    message: FlowMessage


class LocationTemplate(BaseTemplate):
    typ: Literal["location"] = "location"
    message: LocationMessage


class CatalogTemplate(BaseTemplate):
    typ: Literal["catalog"] = "catalog"
    message: CatalogMessage


class ProductTemplate(BaseTemplate):
    typ: Literal["product"] = "product"
    message: ProductMessage


class MultiProductTemplate(BaseTemplate):
    typ: Literal["products"] = "products"
    message: ProductsMessage


# ----------
# Discriminated Union Type
# ----------
EngineTemplate = Annotated[
    Union[
        ButtonTemplate,
        CtaTemplate,
        ListTemplate,
        TextTemplate,
        TemplateTemplate,
        DynamicTemplate,
        MediaTemplate,
        FlowTemplate,
        LocationTemplate,
        RequestLocationTemplate,
        CatalogTemplate,
        ProductTemplate,
        MultiProductTemplate
    ],
    Field(discriminator="typ"),
]


# ----------
# Parsing Function
# ----------
def load_template(data: dict) -> EngineTemplate:
    return EngineTemplate.model_validate(data)
