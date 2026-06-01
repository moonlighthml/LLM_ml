import json
from pathlib import Path

from app.core.config import settings
from app.models.chat import ChatRequest, ChatResponse
from app.models.llm import ModelConfig
from app.services.llm.base import LLMProvider
from app.services.llm.demo import DemoProvider
from app.services.llm.openai_compatible import OpenAICompatibleProvider


class LLMRegistry:
    def __init__(self) -> None:
        self.providers: dict[str, LLMProvider] = {
            DemoProvider.provider_name: DemoProvider(),
            OpenAICompatibleProvider.provider_name: OpenAICompatibleProvider(),
        }
        self.default_model_id, self.models = self._load_models()

    def _load_models(self) -> tuple[str, list[ModelConfig]]:
        raw_path = Path(settings.llm_config_path)
        backend_root = Path(__file__).resolve().parents[3]
        repo_root = backend_root.parent
        candidates = [
            raw_path if raw_path.is_absolute() else Path.cwd() / raw_path,
            backend_root / raw_path,
            repo_root / raw_path,
        ]
        path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])

        if not path.exists():
            return settings.default_model_id, [
                ModelConfig(provider="demo", model_id="demo-local", label="本地演示模型", enabled=True)
            ]

        data = json.loads(path.read_text(encoding="utf-8"))
        models = [ModelConfig(**item) for item in data.get("models", []) if item.get("enabled", True)]
        default_model_id = data.get("default_model_id") or settings.default_model_id
        return default_model_id, models

    async def chat(self, request: ChatRequest) -> ChatResponse:
        model_id = request.model_id or self.default_model_id
        model = next((item for item in self.models if item.model_id == model_id), None)
        if model is None:
            raise KeyError(f"未知 model_id：{model_id}")

        provider = self.providers.get(model.provider)
        if provider is None:
            raise KeyError(f"未知供应商：{model.provider}")

        return await provider.chat(request, model)


llm_registry = LLMRegistry()
