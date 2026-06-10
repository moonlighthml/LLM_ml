import asyncio

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.models.chat import ChatResponse
from app.models.tools import WebSearchRequest, WebSearchResponse, WebSearchResult
from app.services.search_logging import extract_thinking_blocks, model_output_record
from app.services.tools.web_search import _search_duckduckgo


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_models() -> None:
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    model_ids = {model["model_id"] for model in data["models"]}
    assert data["default_model_id"] in model_ids


def test_chat_demo() -> None:
    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "hello"}], "model_id": "demo-local"},
    )
    assert response.status_code == 200
    assert "hello" in response.json()["content"]


def test_list_configured_skills() -> None:
    response = client.get("/api/skills")
    assert response.status_code == 200
    skills = response.json()["skills"]
    assert any(skill["tool"] == "search_web" for skill in skills)


def test_chat_triggers_web_search_skill(monkeypatch) -> None:
    async def fake_search_web(request):
        return WebSearchResponse(
            query=request.query,
            results=[
                WebSearchResult(
                    title="Kobe Bryant - NBA official profile",
                    url="https://www.nba.com/stats/player/977/career",
                    snippet="NBA official player profile with career statistics and basic information.",
                    source="test double",
                )
            ],
            note="test double result.",
        )

    monkeypatch.setattr("app.services.chat_orchestrator.search_web", fake_search_web)
    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "搜索科比的个人主页"}], "model_id": "demo-local"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Kobe Bryant" in data["content"]
    assert data["tool_calls"] == []
    assert data["references"] == []


def test_search_run_logs_model_raw_output(monkeypatch) -> None:
    captured = {}

    async def fake_search_web(request):
        return WebSearchResponse(
            query=request.query,
            results=[
                WebSearchResult(
                    title="Kobe Bryant - Wikipedia",
                    url="https://en.wikipedia.org/wiki/Kobe_Bryant",
                    snippet="Kobe Bryant encyclopedia profile.",
                    source="test double",
                )
            ],
            note="test double result.",
        )

    def fake_append_search_run_log(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("app.services.chat_orchestrator.search_web", fake_search_web)
    monkeypatch.setattr("app.services.chat_orchestrator.append_search_run_log", fake_append_search_run_log)

    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "检索科比"}], "model_id": "demo-local"},
    )

    assert response.status_code == 200
    assert captured["user_text"] == "检索科比"
    assert captured["search_response"].results[0].url == "https://en.wikipedia.org/wiki/Kobe_Bryant"
    assert captured["recommended_homepage"]["url"] == "https://en.wikipedia.org/wiki/Kobe_Bryant"
    assert captured["model_outputs"][0]["raw_output"]
    assert "thinking" in captured["model_outputs"][0]


def test_model_output_record_extracts_thinking() -> None:
    response = ChatResponse(model_id="test-model", content="<think>hidden reasoning</think>\nfinal answer")
    record = model_output_record(response)

    assert extract_thinking_blocks(response.content) == ["hidden reasoning"]
    assert record["raw_output"] == response.content
    assert record["thinking"] == ["hidden reasoning"]


def test_duckduckgo_html_parser(monkeypatch) -> None:
    html = """
    <html>
      <body>
        <a class="result__a" href="/l/?uddg=https%3A%2F%2Fexample.com%2Fprofile">Example Profile</a>
        <a class="result__snippet">Official profile snippet.</a>
      </body>
    </html>
    """

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> None:
            return None

        async def get(self, *args, **kwargs):
            return httpx.Response(200, text=html, request=httpx.Request("GET", "https://html.duckduckgo.com/html/"))

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

    response = asyncio.run(_search_duckduckgo(WebSearchRequest(query="example", limit=1)))
    assert response.note == "Searched DuckDuckGo."
    assert response.results[0].title == "Example Profile"
    assert response.results[0].url == "https://example.com/profile"
    assert response.results[0].snippet == "Official profile snippet."
