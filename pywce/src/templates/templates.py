from typing import Literal, Annotated

from pydantic import TypeAdapter

from pywce.src.constants import TemplateTypeConstants
from pywce.src.templates.base_model import BaseTemplate
from pywce.src.templates.messages import *


# message: str only     =======================================
class TextTemplate(BaseTemplate):
    kind: Literal["text"] = TemplateTypeConstants.TEXT
    message: str


class DynamicTemplate(BaseTemplate):
    kind: Literal["dynamic"] = TemplateTypeConstants.DYNAMIC
    message: str


class RequestLocationTemplate(BaseTemplate):
    kind: Literal["request-location"] = TemplateTypeConstants.REQUEST_LOCATION
    message: str


# ============================================================

class ButtonTemplate(BaseTemplate):
    kind: Literal["button"] = TemplateTypeConstants.BUTTON
    message: ButtonMessage


class CtaTemplate(BaseTemplate):
    kind: Literal["cta"] = TemplateTypeConstants.CTA
    message: CTAMessage


class ListTemplate(BaseTemplate):
    kind: Literal["list"] = TemplateTypeConstants.LIST
    message: ListMessage


class TemplateTemplate(BaseTemplate):
    kind: Literal["templates"] = TemplateTypeConstants.TEMPLATE
    message: TemplateMessage


class MediaTemplate(BaseTemplate):
    kind: Literal["media"] = TemplateTypeConstants.MEDIA
    message: MediaMessage


class FlowTemplate(BaseTemplate):
    kind: Literal["flow"] = TemplateTypeConstants.FLOW
    message: FlowMessage


class LocationTemplate(BaseTemplate):
    kind: Literal["location"] = TemplateTypeConstants.LOCATION
    message: LocationMessage


class CatalogTemplate(BaseTemplate):
    kind: Literal["catalog"] = TemplateTypeConstants.CATALOG
    message: CatalogMessage


class ProductTemplate(BaseTemplate):
    kind: Literal["product"] = TemplateTypeConstants.SINGLE_PRODUCT
    message: ProductMessage


class MultiProductTemplate(BaseTemplate):
    kind: Literal["products"] = TemplateTypeConstants.MULTI_PRODUCT
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
    Field(discriminator=TemplateConstants.TEMPLATE_TYPE),
]


def load_template(data: dict) -> EngineTemplate:
    return TypeAdapter(EngineTemplate).validate_python(data)
