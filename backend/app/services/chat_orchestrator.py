import re

from app.models.chat import ChatMessage, ChatRequest, ChatResponse
from app.models.tools import WebSearchRequest
from app.services.llm.registry import llm_registry
from app.services.skills.registry import get_web_research_skill, should_use_web_search_skill
from app.services.tools.web_search import search_web


def _last_user_text(request: ChatRequest) -> str:
    return next((message.content for message in reversed(request.messages) if message.role == "user"), "")


def _strip_think_blocks(content: str) -> str:
    without_closed_blocks = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    return re.sub(r"<think>.*", "", without_closed_blocks, flags=re.DOTALL).strip()


async def run_chat(request: ChatRequest) -> ChatResponse:
    user_text = _last_user_text(request)
    augmented_messages = list(request.messages)

    if should_use_web_search_skill(user_text):
        skill = get_web_research_skill()
        search_response = await search_web(WebSearchRequest(query=user_text, limit=5))
        skill_instructions = skill.instructions if skill else "进行网页检索，并优先识别官方主页或权威资料页。"

        if search_response.results:
            search_context = "\n".join(
                f"- {result.title}\n  链接：{result.url}\n  摘要：{result.snippet}"
                for result in search_response.results
            )
        else:
            search_context = (
                f"本次内部检索没有拿到可用网页结果。检索状态：{search_response.note}\n"
                "如果检索不可用或没有结果，请明确说明当前无法确认个人主页链接，不要编造网址或来源。"
            )

        augmented_messages = [
            ChatMessage(
                role="system",
                content=(
                    "你已配置 web-research-homepages skill。该 skill 只用于内部增强回答，"
                    "不要向用户暴露工具调用流程，也不要输出 <think> 标签或思考过程。"
                    "只有在内部检索结果提供了可核验链接时，才给出主页或资料页链接。\n\n"
                    f"{skill_instructions}"
                ),
            ),
            ChatMessage(role="user", content=user_text),
            ChatMessage(
                role="user",
                content=f"内部检索结果如下，请用于增强回答，不要把这段内部提示原样复述给用户：\n{search_context}",
            ),
        ]

    llm_response = await llm_registry.chat(
        request.model_copy(update={"messages": augmented_messages, "tools": ["search_web"]})
    )
    llm_response.content = _strip_think_blocks(llm_response.content)
    llm_response.tool_calls = []
    llm_response.references = []
    return llm_response
