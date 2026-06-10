import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.chat import ChatResponse
from app.models.tools import WebSearchResponse

REPO_ROOT = Path(__file__).resolve().parents[3]
SEARCH_LOG_PATH = REPO_ROOT / "logs" / "search-runs.jsonl"


def extract_thinking_blocks(content: str) -> list[str]:
    blocks = [match.strip() for match in re.findall(r"<think>(.*?)</think>", content, flags=re.DOTALL)]
    open_block = re.search(r"<think>(.*)", content, flags=re.DOTALL)
    if open_block and not re.search(r"</think>", open_block.group(1), flags=re.DOTALL):
        blocks.append(open_block.group(1).strip())
    return [block for block in blocks if block]


def model_output_record(response: ChatResponse) -> dict[str, Any]:
    return {
        "model_id": response.model_id,
        "raw_output": response.content,
        "thinking": extract_thinking_blocks(response.content),
        "tool_calls": [tool_call.model_dump() for tool_call in response.tool_calls],
    }


def append_search_run_log(
    *,
    user_text: str,
    search_response: WebSearchResponse,
    model_outputs: list[dict[str, Any]],
    final_content: str,
    recommended_homepage: dict[str, str] | None,
) -> None:
    SEARCH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_text": user_text,
        "search": search_response.model_dump(),
        "recommended_homepage": recommended_homepage,
        "model_outputs": model_outputs,
        "final_content": final_content,
    }
    with SEARCH_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")
