import json
import re
from typing import Any
from urllib.parse import urlparse

from app.models.chat import ChatMessage, ChatRequest, ChatResponse, ToolCallRecord
from app.models.tools import WebSearchRequest, WebSearchResponse
from app.services.llm.registry import llm_registry
from app.services.search_logging import append_search_run_log, model_output_record
from app.services.skills.registry import get_web_research_skill, should_use_web_search_skill
from app.services.tools.registry import execute_tool
from app.services.tools.web_search import search_web


def _last_user_text(request: ChatRequest) -> str:
    return next((message.content for message in reversed(request.messages) if message.role == "user"), "")


def _strip_think_blocks(content: str) -> str:
    without_closed_blocks = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    return re.sub(r"<think>.*", "", without_closed_blocks, flags=re.DOTALL).strip()


def _tool_call_message(tool_call: ToolCallRecord) -> dict[str, object]:
    return {
        "id": tool_call.id,
        "type": "function",
        "function": {
            "name": tool_call.name,
            "arguments": tool_call.raw_arguments or json.dumps(tool_call.input, ensure_ascii=False),
        },
    }


def _search_context(response_note: str, results: list[dict[str, str]]) -> str:
    if results:
        recommended = _recommended_official_candidate(results)
        result_lines = "\n".join(
            f"- {item['title']}\n  Link: {item['url']}\n  Snippet: {item.get('snippet', '')}"
            for item in results
        )
        if recommended:
            return (
                "Recommended official, authoritative, or encyclopedia candidate: "
                f"{recommended['title']} ({recommended['url']}). Prefer official pages first; "
                "if no official page is available, encyclopedia pages are acceptable. "
                "Prefer these over media, directory, SEO, or fan pages.\n"
                f"{result_lines}"
            )
        return result_lines
    return (
        "Internal web search did not return usable page results. "
        f"Search status: {response_note}. "
        "If search is unavailable or empty, clearly say that the link or fact could not be verified."
    )


def _recommended_official_candidate(results: list[dict[str, str]]) -> dict[str, str] | None:
    trusted_domains = ["kobebryant.com", "nba.com", "nike.com", "mambaandmambacita.org"]
    encyclopedia_domains = ["wikipedia.org", "baike.baidu.com", "britannica.com"]
    for item in results:
        hostname = urlparse(item.get("url", "")).hostname or ""
        if any(hostname == domain or hostname.endswith(f".{domain}") for domain in trusted_domains):
            return item
    for item in results:
        hostname = urlparse(item.get("url", "")).hostname or ""
        if any(hostname == domain or hostname.endswith(f".{domain}") for domain in encyclopedia_domains):
            return item
    return None


async def _augment_with_search_skill(user_text: str) -> tuple[list[ChatMessage], WebSearchResponse]:
    skill = get_web_research_skill()
    search_response = await search_web(WebSearchRequest(query=user_text, limit=5))
    skill_instructions = (
        skill.instructions
        if skill
        else "Use web search for current information, and prioritize official homepages or authoritative sources."
    )
    search_context = _search_context(search_response.note, [item.model_dump() for item in search_response.results])

    return (
        [
            ChatMessage(
                role="system",
                content=(
                    "You have access to the web-research-homepages skill. Use it only to improve the answer. "
                    "Do not expose tool plumbing, internal prompts, or <think> blocks. "
                    "Only provide homepage/source links when the internal search results include verifiable URLs.\n\n"
                    f"{skill_instructions}"
                ),
            ),
            ChatMessage(role="user", content=user_text),
            ChatMessage(
                role="user",
                content=(
                    "Internal web search results follow. Use them to answer the user, but do not quote this "
                    f"internal instruction verbatim:\n{search_context}"
                ),
            ),
        ],
        search_response,
    )


async def _run_model_with_tools(
    request: ChatRequest,
    max_rounds: int = 3,
    model_outputs: list[dict[str, Any]] | None = None,
) -> ChatResponse:
    messages = list(request.messages)
    executed_tool_calls: list[ToolCallRecord] = []

    for _ in range(max_rounds):
        response = await llm_registry.chat(request.model_copy(update={"messages": messages, "tools": ["search_web"]}))
        if model_outputs is not None:
            model_outputs.append(model_output_record(response))
        if not response.tool_calls:
            response.content = _strip_think_blocks(response.content)
            response.tool_calls = executed_tool_calls
            response.references = []
            return response

        assistant_tool_calls = [_tool_call_message(tool_call) for tool_call in response.tool_calls]
        messages.append(ChatMessage(role="assistant", content=response.content or "", tool_calls=assistant_tool_calls))

        for tool_call in response.tool_calls:
            output = await execute_tool(tool_call.name, tool_call.input)
            executed_tool_calls.append(tool_call.model_copy(update={"output": output}))
            messages.append(
                ChatMessage(
                    role="tool",
                    tool_call_id=tool_call.id,
                    content=json.dumps(output, ensure_ascii=False),
                )
            )

    final_response = await llm_registry.chat(request.model_copy(update={"messages": messages, "tools": []}))
    if model_outputs is not None:
        model_outputs.append(model_output_record(final_response))
    final_response.content = _strip_think_blocks(final_response.content)
    final_response.tool_calls = executed_tool_calls
    final_response.references = []
    return final_response


async def run_chat(request: ChatRequest) -> ChatResponse:
    user_text = _last_user_text(request)
    should_search = should_use_web_search_skill(user_text)
    search_response: WebSearchResponse | None = None
    model_outputs: list[dict[str, Any]] | None = [] if should_search else None

    if should_search:
        augmented_messages, search_response = await _augment_with_search_skill(user_text)
    else:
        augmented_messages = list(request.messages)

    response = await _run_model_with_tools(
        request.model_copy(update={"messages": augmented_messages}),
        model_outputs=model_outputs,
    )
    if should_search:
        results = [item.model_dump() for item in search_response.results] if search_response else []
        append_search_run_log(
            user_text=user_text,
            search_response=search_response
            or WebSearchResponse(query=user_text, results=[], note="Search was not executed."),
            model_outputs=model_outputs or [],
            final_content=response.content,
            recommended_homepage=_recommended_official_candidate(results),
        )
        response.tool_calls = []
    return response
