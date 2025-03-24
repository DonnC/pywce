from typing import Dict, Optional, Any

from pydantic import BaseModel, Field

from pywce.src.constants import TemplateConstants


# ----------
# Base Message Model (for each template type inner message)
# ----------
class BaseMessage(BaseModel):
    pass


# ----------
# Template Models (with type-specific subclasses)
# ----------
class BaseTemplate(BaseModel):
    typ: str = Field(..., alias=TemplateConstants.TEMPLATE_TYPE)
    routes: Dict[str, str]

    # attr
    acknowledge: Optional[bool] = Field(..., alias=TemplateConstants.READ_RECEIPT)
    authenticated: Optional[bool] = None
    checkpoint: Optional[bool] = None
    prop: Optional[str] = None
    session: Optional[bool] = None
    transient: Optional[bool] = None
    reply_message_id: Optional[str] = Field(..., alias=TemplateConstants.REPLY_MESSAGE_ID)

    # hooks
    template: Optional[str] = None
    on_receive: Optional[str] = Field(None, alias=TemplateConstants.ON_RECEIVE)
    on_generate: Optional[str] = Field(None, alias=TemplateConstants.ON_GENERATE)
    validator: Optional[str] = None
    router: Optional[str] = None
    middleware: Optional[str] = None

    params: Optional[Dict[Any, Any]] = None
