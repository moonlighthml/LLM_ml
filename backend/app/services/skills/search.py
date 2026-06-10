import re
from pathlib import Path

from app.models.skills import SkillResult, SkillSearchRequest, SkillSearchResponse
from app.services.skills.registry import SKILLS_DIR, list_configured_skills


def _query_terms(query: str) -> set[str]:
    normalized = query.lower()
    terms = {term for term in re.split(r"\s+", normalized) if term.strip()}
    known_terms = [
        "搜索",
        "检索",
        "查找",
        "联网",
        "个人主页",
        "主页",
        "官网",
        "人物",
        "链接",
        "homepage",
        "search",
        "profile",
        "official",
    ]
    terms.update(term.lower() for term in known_terms if term.lower() in normalized)
    return terms


def _score_skill(query_terms: set[str], haystack: str) -> int:
    if not query_terms:
        return 1
    return sum(1 for term in query_terms if term in haystack)


def search_skills(request: SkillSearchRequest) -> SkillSearchResponse:
    query_terms = _query_terms(request.query)
    results: list[SkillResult] = []

    for skill in list_configured_skills().skills:
        haystack = " ".join(
            [
                skill.name,
                skill.description,
                " ".join(skill.tags),
                " ".join(skill.triggers),
                skill.instructions,
            ]
        ).lower()
        score = _score_skill(query_terms, haystack)
        if score > 0:
            path = Path(SKILLS_DIR / skill.name / "SKILL.md")
            results.append(
                SkillResult(
                    name=skill.name,
                    description=skill.description,
                    tags=skill.tags,
                    score=score,
                    path=str(path),
                )
            )

    results.sort(key=lambda item: item.score, reverse=True)
    return SkillSearchResponse(query=request.query, results=results[: request.limit])
