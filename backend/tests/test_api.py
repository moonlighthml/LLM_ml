from fastapi.testclient import TestClient

from app.main import app


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


def test_chat_triggers_web_search_skill() -> None:
    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "搜索科比的个人主页"}], "model_id": "demo-local"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tool_calls"][0]["name"] == "search_web"
    assert data["references"][0]["url"].startswith("https://")
