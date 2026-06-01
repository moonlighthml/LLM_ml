from app.models.chat import ChatRequest, ChatResponse
from app.models.llm import ModelConfig
from app.services.llm.base import LLMProvider


class DemoProvider(LLMProvider):
    provider_name = "demo"

    async def chat(self, request: ChatRequest, model: ModelConfig) -> ChatResponse:
        last_user_message = next(
            (message.content for message in reversed(request.messages) if message.role == "user"),
            "",
        )
        content = (
            "本地演示适配器响应。后续可以在不改动聊天 API 的前提下新增真实 LLM 供应商。\n\n"
            f"用户输入：{last_user_message}"
        )
        return ChatResponse(model_id=model.model_id, content=content)
