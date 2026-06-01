from abc import ABC, abstractmethod

from app.models.chat import ChatRequest, ChatResponse
from app.models.llm import ModelConfig


class LLMProvider(ABC):
    provider_name: str

    @abstractmethod
    async def chat(self, request: ChatRequest, model: ModelConfig) -> ChatResponse:
        raise NotImplementedError

