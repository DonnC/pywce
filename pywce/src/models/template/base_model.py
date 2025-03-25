from typing import Dict, Optional, Any, List, Union

from pydantic import BaseModel, Field, field_validator

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
# Base Message Model (for each template type inner message)
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
    acknowledge: Optional[bool] = Field(None, alias=TemplateConstants.READ_RECEIPT)
    authenticated: Optional[bool] = None
    checkpoint: Optional[bool] = None
    prop: Optional[str] = None
    session: Optional[bool] = None
    transient: Optional[bool] = None
    reply_message_id: Optional[str] = Field(None, alias=TemplateConstants.REPLY_MESSAGE_ID)

    # hooks
    template: Optional[str] = None
    on_receive: Optional[str] = Field(None, alias=TemplateConstants.ON_RECEIVE)
    on_generate: Optional[str] = Field(None, alias=TemplateConstants.ON_GENERATE)
    validator: Optional[str] = None
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
