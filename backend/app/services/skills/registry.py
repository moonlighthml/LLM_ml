import json
from pathlib import Path

from app.models.skills import ConfiguredSkill, SkillListResponse

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILLS_DIR = REPO_ROOT / "skills"


def list_configured_skills() -> SkillListResponse:
    skills: list[ConfiguredSkill] = []
    for path in sorted(SKILLS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        skills.append(
            ConfiguredSkill(
                name=data.get("name", path.stem),
                description=data.get("description", ""),
                tags=data.get("tags", []),
                tool=data.get("tool", ""),
                triggers=data.get("triggers", []),
            )
        )
    return SkillListResponse(skills=skills)


def should_use_web_search_skill(text: str) -> bool:
    lowered = text.lower()
    action_hit = any(keyword in lowered for keyword in ["搜索", "检索", "查找", "search", "find"])
    target_hit = any(keyword in lowered for keyword in ["个人主页", "主页", "官网", "链接", "homepage", "profile"])
    return action_hit and target_hit
