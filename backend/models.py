from pydantic import BaseModel, Field
from typing import Optional


class SearchRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=40)
    categories: Optional[list[str]] = None
    include_nsfw: bool = False
    deep_mode: bool = False


class SearchResponse(BaseModel):
    search_id: str
    username: str
    total: int
    found: int
    not_found: int
    errors: int
    results: list[dict]
