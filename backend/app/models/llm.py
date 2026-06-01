from pydantic import BaseModel, ConfigDict


class ModelConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: str
    model_id: str
    label: str
    base_url: str | None = None
    api_key_env: str | None = None
    stream: bool = True
    tools: bool = True
    temperature: float = 0.7
    max_tokens: int = 2048
    enabled: bool = True

    def public_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model_id": self.model_id,
            "label": self.label,
            "stream": self.stream,
            "tools": self.tools,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "enabled": self.enabled,
        }
