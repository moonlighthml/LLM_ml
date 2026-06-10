from pathlib import Path

from app.models.skills import ConfiguredSkill, SkillListResponse

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILLS_DIR = REPO_ROOT / "skills"

WEB_SEARCH_ACTION_KEYWORDS = [
    "搜索",
    "检索",
    "查找",
    "浏览",
    "核实",
    "验证",
    "研究",
    "联网",
    "search",
    "find",
    "look up",
    "browse",
    "verify",
    "research",
]
WEB_SEARCH_ENTITY_KEYWORDS = [
    "主页",
    "官网",
    "个人主页",
    "公司官网",
    "组织",
    "品牌",
    "人物",
    "homepage",
    "official",
    "profile",
    "company",
]


def _parse_skill_markdown(path: Path) -> ConfiguredSkill:
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    body = text

    if text.startswith("---"):
        _, frontmatter, body = text.split("---", 2)
        for line in frontmatter.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip('"')

    name = metadata.get("name", path.parent.name)
    description = metadata.get("description", "")
    return ConfiguredSkill(
        name=name,
        description=description,
        tags=["web search", "official homepage", "sources"],
        tool="search_web",
        triggers=WEB_SEARCH_ACTION_KEYWORDS + WEB_SEARCH_ENTITY_KEYWORDS,
        instructions=body.strip(),
    )


def list_configured_skills() -> SkillListResponse:
    skills: list[ConfiguredSkill] = []
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        skills.append(_parse_skill_markdown(path))
    return SkillListResponse(skills=skills)


def get_web_research_skill() -> ConfiguredSkill | None:
    for skill in list_configured_skills().skills:
        if skill.name == "web-research-homepages":
            return skill
    return None


def should_use_web_search_skill(text: str) -> bool:
    lowered = text.lower()
    action_hit = any(keyword in lowered for keyword in WEB_SEARCH_ACTION_KEYWORDS)
    entity_hit = any(keyword in lowered for keyword in WEB_SEARCH_ENTITY_KEYWORDS)
    return action_hit or entity_hit
