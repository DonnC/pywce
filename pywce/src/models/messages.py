from typing import Dict, List, Optional

from pydantic import Field

from pywce.src.constants import TemplateConstants
from pywce.src.models.base_model import BaseMessage
from pywce.src.models.inner_message import ListSection


class BaseInteractiveMessage(BaseMessage):
    body: str
    title: Optional[str] = None
    footer: Optional[str] = None


# Message Models for Each Type
class ButtonMessage(BaseInteractiveMessage):
    buttons: List[str] = Field(..., alias=TemplateConstants.MESSAGE_BUTTONS)


class CatalogMessage(BaseInteractiveMessage):
    product_id: str = Field(..., alias=TemplateConstants.MESSAGE_CATALOG_PRODUCT_ID)


class ProductMessage(BaseInteractiveMessage):
    catalog_id: str = Field(..., alias=TemplateConstants.MESSAGE_CATALOG_ID)
    product_id: str = Field(..., alias=TemplateConstants.MESSAGE_CATALOG_PRODUCT_ID)


class ProductsMessage(BaseInteractiveMessage):
    catalog_id: str = Field(..., alias=TemplateConstants.MESSAGE_CATALOG_ID)
    button: str
    sections: Dict[str, List[str]]  # {section_title: [product_ids]}


class CTAMessage(BaseInteractiveMessage):
    url: str
    button: str


class TemplateMessage(BaseMessage):
    name: str
    language: Optional[str] = "en_US"


class ListMessage(BaseInteractiveMessage):
    button: str
    sections: List[ListSection]


class MediaMessage(BaseMessage):
    typ: str = Field(..., alias=TemplateConstants.TEMPLATE_TYPE)
    media_id: Optional[str] = Field(..., alias=TemplateConstants.MESSAGE_ID)
    url: Optional[str] = None
    caption: Optional[str] = None
    filename: Optional[str] = None


class FlowMessage(BaseInteractiveMessage):
    flow_id: Optional[str] = Field(..., alias="id")
    draft: bool = False
    name: str
    button: str


class LocationMessage(BaseMessage):
    lat: str
    lon: str
    name: Optional[str] = None
    address: Optional[str] = None
