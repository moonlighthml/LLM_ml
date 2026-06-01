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
            "Demo adapter response. Real LLM providers can be added without changing the chat API.\n\n"
            f"User said: {last_user_message}"
        )
        return ChatResponse(model_id=model.model_id, content=content)

