from pydantic import BaseModel, Field


class SkillSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=20)


class SkillResult(BaseModel):
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    score: int
    path: str


class SkillSearchResponse(BaseModel):
    query: str
    results: list[SkillResult]

