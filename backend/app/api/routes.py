from fastapi import APIRouter, HTTPException

from app.models.chat import ChatRequest, ChatResponse
from app.models.skills import SkillSearchRequest, SkillSearchResponse
from app.models.tools import WebSearchRequest, WebSearchResponse
from app.services.llm.registry import llm_registry
from app.services.skills.search import search_skills
from app.services.tools.web_search import search_web

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/models")
async def models() -> dict[str, object]:
    return {
        "default_model_id": llm_registry.default_model_id,
        "models": [model.public_dict() for model in llm_registry.models],
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await llm_registry.chat(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/skills/search", response_model=SkillSearchResponse)
async def skills_search(request: SkillSearchRequest) -> SkillSearchResponse:
    return search_skills(request)


@router.post("/tools/search-web", response_model=WebSearchResponse)
async def web_search(request: WebSearchRequest) -> WebSearchResponse:
    return await search_web(request)

