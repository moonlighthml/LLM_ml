import json
import re
from pathlib import Path

from app.models.skills import SkillResult, SkillSearchRequest, SkillSearchResponse

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILLS_DIR = REPO_ROOT / "skills"


def _query_terms(query: str) -> set[str]:
    terms = {term.lower() for term in re.split(r"\s+", query) if term.strip()}
    known_terms = ["搜索", "查找", "个人主页", "主页", "人物", "链接", "homepage", "search", "profile"]
    terms.update(term.lower() for term in known_terms if term.lower() in query.lower())
    return terms


def search_skills(request: SkillSearchRequest) -> SkillSearchResponse:
    query_terms = _query_terms(request.query)
    results: list[SkillResult] = []

    for path in sorted(SKILLS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        haystack = " ".join(
            [
                data.get("name", ""),
                data.get("description", ""),
                " ".join(data.get("tags", [])),
                data.get("instructions", ""),
            ]
        ).lower()
        score = sum(1 for term in query_terms if term in haystack)
        if score > 0 or not query_terms:
            results.append(
                SkillResult(
                    name=data.get("name", path.stem),
                    description=data.get("description", ""),
                    tags=data.get("tags", []),
                    score=score,
                    path=str(path),
                )
            )

    results.sort(key=lambda item: item.score, reverse=True)
    return SkillSearchResponse(query=request.query, results=results[: request.limit])
