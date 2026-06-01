from pathlib import Path

from app.models.skills import ConfiguredSkill, SkillListResponse

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILLS_DIR = REPO_ROOT / "skills"


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
    triggers = [
        "搜索",
        "检索",
        "查找",
        "浏览",
        "核实",
        "研究",
        "主页",
        "官网",
        "个人主页",
        "公司官网",
        "look up",
        "browse",
        "verify",
        "research",
        "homepage",
        "official",
        "profile",
    ]
    tags = ["网页检索", "官方主页", "来源引用"]
    return ConfiguredSkill(
        name=name,
        description=description,
        tags=tags,
        tool="search_web",
        triggers=triggers,
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
    action_hit = any(
        keyword in lowered
        for keyword in ["搜索", "检索", "查找", "浏览", "核实", "研究", "search", "find", "browse", "verify", "research"]
    )
    entity_hit = any(
        keyword in lowered
        for keyword in ["主页", "官网", "个人", "公司", "组织", "品牌", "人物", "homepage", "official", "profile", "company"]
    )
    return action_hit or entity_hit
