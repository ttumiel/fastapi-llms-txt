from typing import Dict, List, Optional

from pydantic import BaseModel, HttpUrl


class LinkItem(BaseModel):
    """Represents a single link item in a section."""

    title: str
    url: HttpUrl


class ProjectDescription(BaseModel):
    """Schema for the project description in llms.txt."""

    title: str
    summary: str
    notes: Optional[List[str]] = None
    sections: Dict[str, List[LinkItem]]
