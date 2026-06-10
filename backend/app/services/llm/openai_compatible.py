import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

from app.models.chat import ChatRequest, ChatResponse
from app.models.llm import ModelConfig
from app.services.llm.base import LLMProvider
from app.services.tools.registry import get_tool_schemas, parse_tool_arguments


REPO_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(REPO_ROOT / ".env")


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
            "messages": [
                message.model_dump(exclude_none=True)
                for message in request.messages
            ],
            "temperature": request.temperature if request.temperature is not None else model.temperature,
            "max_tokens": request.max_tokens if request.max_tokens is not None else model.max_tokens,
            "stream": False,
        }
        if request.tools and model.tools:
            tool_schemas = get_tool_schemas(request.tools)
            if tool_schemas:
                payload["tools"] = tool_schemas
                payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{model.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        message = data["choices"][0]["message"]
        content = message.get("content") or ""
        tool_calls = []
        for tool_call in message.get("tool_calls") or []:
            function = tool_call.get("function") or {}
            name = function.get("name")
            if not name:
                continue
            raw_arguments = function.get("arguments", "{}")
            tool_calls.append(
                {
                    "name": name,
                    "id": tool_call.get("id"),
                    "input": parse_tool_arguments(raw_arguments),
                    "raw_arguments": raw_arguments,
                }
            )
        return ChatResponse(model_id=model.model_id, content=content, tool_calls=tool_calls)
