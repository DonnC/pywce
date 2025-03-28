from typing import Annotated

from pydantic import TypeAdapter

from .base_model import *
from .messages import *
from .templates import *

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

class Template:
    @staticmethod
    def as_model(template: dict) -> EngineTemplate:
        return TypeAdapter(EngineTemplate).validate_python(template)

    @staticmethod
    def as_dict(template: EngineTemplate) -> dict:
        return template.model_dump(by_alias=True)
