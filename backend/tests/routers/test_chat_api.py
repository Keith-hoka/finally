"""Chat endpoint tests in mock mode."""

import pytest


@pytest.fixture
def mock_llm(monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")


def test_chat_buy_roundtrip(mock_llm, client, cache):
    cache.update("AAPL", 100.0)
    response = client.post("/api/chat", json={"message": "buy AAPL please"})

    assert response.status_code == 200
    body = response.json()
    assert "Mock" in body["message"]
    assert body["actions"]["trades"][0]["ticker"] == "AAPL"


def test_chat_history_endpoint(mock_llm, client, cache):
    cache.update("AAPL", 100.0)
    client.post("/api/chat", json={"message": "buy AAPL"})

    response = client.get("/api/chat/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["actions"] is None
    assert history[1]["role"] == "assistant"
    assert history[1]["actions"]["trades"][0]["ticker"] == "AAPL"


def test_chat_unavailable_without_key_is_503(monkeypatch, client):
    monkeypatch.delenv("LLM_MOCK", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    response = client.post("/api/chat", json={"message": "hello"})

    assert response.status_code == 503
    assert "OPENROUTER_API_KEY" in response.json()["detail"]
