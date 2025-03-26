from typing import List, Optional, Union

from pydantic import Field, field_validator

from pywce.src.constants import TemplateConstants
from pywce.src.templates.base_model import BaseMessage, ListSection, SectionRowItem, ProductsListSection


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
    sections: List[ProductsListSection]

    @field_validator('sections', mode='before')
    @classmethod
    def from_dict_(cls, value: dict):
        sections_list = [
            ProductsListSection(
                title=str(section_name),
                products=product_ids
            )
            for section_name, product_ids in value.items()
        ]
        return sections_list


class CTAMessage(BaseInteractiveMessage):
    url: str
    button: str


class TemplateMessage(BaseMessage):
    name: str
    language: Optional[str] = "en_US"


class ListMessage(BaseInteractiveMessage):
    button: str
    sections: List[ListSection]

    @field_validator('sections', mode='before')
    @classmethod
    def from_dict_(cls, value: dict):
        sections_list = [
            ListSection(
                title=str(section_name),
                rows=[SectionRowItem(identifier=str(_id), **row_data) for _id, row_data in row.items()]
            )
            for section_name, row in value.items()
        ]
        return sections_list


class MediaMessage(BaseMessage):
    kind: str = Field(..., alias=TemplateConstants.TEMPLATE_TYPE)
    media_id: Optional[str] = Field(None, alias=TemplateConstants.MESSAGE_ID)
    url: Optional[str] = None
    caption: Optional[str] = None
    filename: Optional[str] = None


class FlowMessage(BaseInteractiveMessage):
    flow_id: Union[int, str]
    draft: bool = False
    name: str
    button: str


class LocationMessage(BaseMessage):
    lat: str
    lon: str
    name: Optional[str] = None
    address: Optional[str] = None
