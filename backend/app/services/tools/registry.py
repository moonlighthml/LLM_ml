import json
from typing import Any

from app.models.tools import WebSearchRequest
from app.services.tools.web_search import SEARCH_WEB_TOOL_SCHEMA, search_web


TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "search_web": SEARCH_WEB_TOOL_SCHEMA,
}


def get_tool_schemas(names: list[str]) -> list[dict[str, Any]]:
    return [TOOL_SCHEMAS[name] for name in names if name in TOOL_SCHEMAS]


async def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "search_web":
        request = WebSearchRequest(**arguments)
        return (await search_web(request)).model_dump()
    return {"error": f"Unknown tool: {name}"}


def parse_tool_arguments(raw_arguments: str | dict[str, Any] | None) -> dict[str, Any]:
    if raw_arguments is None:
        return {}
    if isinstance(raw_arguments, dict):
        return raw_arguments
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
