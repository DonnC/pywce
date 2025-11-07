from typing import Dict, Optional, Any, List, Union

from pydantic import BaseModel, Field, field_validator, model_serializer

from pywce.src.constants import TemplateConstants, EngineConstants


# Define the EngineRoute model
class EngineRoute(BaseModel):
    user_input: Union[int, str]
    next_stage: str
    is_regex: Optional[bool] = None


class SectionRowItem(BaseModel):
    identifier: Union[int, str]
    title: str
    description: Optional[str] = None

class ListSection(BaseModel):
    title: str
    rows: List[SectionRowItem]

class ProductsListSection(BaseModel):
    title: str
    products: List[str]


# ----------
# Base Message Model (for each templates type inner message)
# ----------
class BaseMessage(BaseModel):
    pass


# ----------
# Template Models (with type-specific subclasses)
# ----------
class BaseTemplate(BaseModel):
    kind: str = Field(..., alias=TemplateConstants.TEMPLATE_TYPE)
    routes: List[EngineRoute]

    # attr
    acknowledge: bool = Field(False, alias=TemplateConstants.READ_RECEIPT)
    authenticated: bool = False
    checkpoint: bool = False
    prop: Optional[str] = None
    session: bool = True
    transient: bool = False
    typing: bool = False
    reply_message_id: Optional[str] = Field(None, alias=TemplateConstants.REPLY_MESSAGE_ID)

    # hooks
    template: Optional[str] = None
    on_receive: Optional[str] = Field(None, alias=TemplateConstants.ON_RECEIVE)
    on_generate: Optional[str] = Field(None, alias=TemplateConstants.ON_GENERATE)
    router: Optional[str] = None
    middleware: Optional[str] = None

    params: Optional[Dict[Any, Any]] = None

    @field_validator('routes', mode='before')
    @classmethod
    def parse_map_routes_to_list(cls, value):
        if isinstance(value, dict):
            return [
                EngineRoute(user_input=k, next_stage=v, is_regex=str(k).startswith(EngineConstants.REGEX_PLACEHOLDER))
                for k, v in value.items()]
        return value

    @model_serializer(mode="wrap")
    def serialize(self, handler):
        """Convert routes back to a dictionary when serializing"""
        data = handler(self)

        if isinstance(self.routes, list):
            data["routes"] = {route.user_input: route.next_stage for route in self.routes}

        return data
