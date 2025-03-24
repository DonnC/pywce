# ----------
# Base Message Model (for each template type inner message)
# ----------
from typing import Optional, List

from pydantic import BaseModel, Field


class ListSectionInnerMessage(BaseModel):
    row_id: str = Field(..., alias="id")
    title: str
    description: Optional[str] = None


class ListSection(BaseModel):
    title: str
    rows: List[ListSectionInnerMessage]