from app.models.chat import ChatMessage, ChatRequest, ChatResponse
from app.models.tools import WebSearchRequest
from app.services.llm.registry import llm_registry
from app.services.skills.registry import should_use_web_search_skill
from app.services.tools.web_search import search_web


def _last_user_text(request: ChatRequest) -> str:
    return next((message.content for message in reversed(request.messages) if message.role == "user"), "")


async def run_chat(request: ChatRequest) -> ChatResponse:
    user_text = _last_user_text(request)
    augmented_messages = list(request.messages)

    if should_use_web_search_skill(user_text):
        search_response = await search_web(WebSearchRequest(query=user_text, limit=5))
        search_context = "\n".join(
            f"- {result.title}\n  链接：{result.url}\n  摘要：{result.snippet}"
            for result in search_response.results
        )
        augmented_messages = [
            ChatMessage(
                role="system",
                content=(
                    "你具备网页检索 skill。后端已经在内部完成检索，"
                    "请自然地基于检索结果回答用户，不要暴露内部工具调用流程。"
                ),
            ),
            *request.messages,
            ChatMessage(
                role="user",
                content=f"内部检索结果如下，请用于增强回答：\n{search_context}",
            ),
        ]

    llm_response = await llm_registry.chat(
        request.model_copy(update={"messages": augmented_messages, "tools": ["search_web"]})
    )
    llm_response.tool_calls = []
    llm_response.references = []
    return llm_response
