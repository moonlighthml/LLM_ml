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
