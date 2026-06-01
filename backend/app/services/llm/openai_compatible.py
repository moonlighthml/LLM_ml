import os
from typing import Any

import httpx

from app.models.chat import ChatRequest, ChatResponse
from app.models.llm import ModelConfig
from app.services.llm.base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    provider_name = "openai-compatible"

    async def chat(self, request: ChatRequest, model: ModelConfig) -> ChatResponse:
        if not model.base_url or not model.api_key_env:
            raise ValueError("OpenAI 兼容模型需要配置 base_url 和 api_key_env。")

        api_key = os.getenv(model.api_key_env)
        if not api_key:
            raise ValueError(f"缺少 API 密钥环境变量：{model.api_key_env}")

        payload: dict[str, Any] = {
            "model": model.model_id,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature if request.temperature is not None else model.temperature,
            "max_tokens": request.max_tokens if request.max_tokens is not None else model.max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{model.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"].get("content", "")
        return ChatResponse(model_id=model.model_id, content=content)
