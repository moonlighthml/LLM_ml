from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class ChatRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    messages: list[ChatMessage]
    model_id: str | None = None
    stream: bool = False
    tools: list[str] = Field(default_factory=list)
    temperature: float | None = None
    max_tokens: int | None = None


class ToolCallRecord(BaseModel):
    name: str
    id: str | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    raw_arguments: str | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    content: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    references: list[dict[str, str]] = Field(default_factory=list)
