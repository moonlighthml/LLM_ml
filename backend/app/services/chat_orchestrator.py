from app.models.chat import ChatMessage, ChatRequest, ChatResponse, ToolCallRecord
from app.models.tools import WebSearchRequest
from app.services.llm.registry import llm_registry
from app.services.skills.registry import should_use_web_search_skill
from app.services.tools.web_search import search_web


def _last_user_text(request: ChatRequest) -> str:
    return next((message.content for message in reversed(request.messages) if message.role == "user"), "")


async def run_chat(request: ChatRequest) -> ChatResponse:
    user_text = _last_user_text(request)
    tool_calls: list[ToolCallRecord] = []
    references: list[dict[str, str]] = []
    augmented_messages = list(request.messages)

    if should_use_web_search_skill(user_text):
        search_response = await search_web(WebSearchRequest(query=user_text, limit=5))
        tool_output = {
            "query": search_response.query,
            "note": search_response.note,
            "results": [result.model_dump() for result in search_response.results],
        }
        tool_calls.append(
            ToolCallRecord(
                name="search_web",
                input={"query": user_text},
                output=tool_output,
            )
        )
        references = [
            {"title": result.title, "url": result.url, "snippet": result.snippet}
            for result in search_response.results
        ]
        search_context = "\n".join(
            f"- {result.title}\n  链接：{result.url}\n  摘要：{result.snippet}"
            for result in search_response.results
        )
        augmented_messages = [
            ChatMessage(
                role="system",
                content=(
                    "你可以使用已配置的网页检索 skill。后端已经完成工具调用，"
                    "请基于工具结果回答用户，并说明链接是否需要人工确认。"
                ),
            ),
            *request.messages,
            ChatMessage(
                role="user",
                content=f"以下是网页检索工具返回的结果，请据此回答：\n{search_context}",
            ),
        ]

    llm_response = await llm_registry.chat(
        request.model_copy(update={"messages": augmented_messages, "tools": ["search_web"]})
    )
    llm_response.tool_calls = tool_calls
    llm_response.references = references
    return llm_response
