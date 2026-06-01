from pydantic import BaseModel, Field


class WebSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=10)


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str = "placeholder"


class WebSearchResponse(BaseModel):
    query: str
    results: list[WebSearchResult]
    note: str

