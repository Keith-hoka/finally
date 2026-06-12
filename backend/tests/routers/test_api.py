"""API route tests: status codes, response shapes, error mapping."""

from app.db import DEFAULT_CASH, DEFAULT_TICKERS


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_portfolio_initial_state(client):
    response = client.get("/api/portfolio")
    assert response.status_code == 200
    body = response.json()
    assert body["cash_balance"] == DEFAULT_CASH
    assert body["total_value"] == DEFAULT_CASH
    assert body["positions"] == []


def test_trade_buy_then_sell(client, cache):
    cache.update("AAPL", 100.0)

    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cash_balance"] == DEFAULT_CASH - 1000.0
    assert body["position_quantity"] == 10

    positions = client.get("/api/portfolio").json()["positions"]
    assert positions[0]["ticker"] == "AAPL"

    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "sell"}
    )
    assert response.status_code == 200
    assert response.json()["cash_balance"] == DEFAULT_CASH
    assert client.get("/api/portfolio").json()["positions"] == []


def test_trade_insufficient_cash_is_400(client, cache):
    cache.update("AAPL", 100.0)
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1000, "side": "buy"}
    )
    assert response.status_code == 400
    assert "Insufficient cash" in response.json()["detail"]


def test_trade_invalid_ticker_is_400(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "TOOLONG", "quantity": 1, "side": "buy"}
    )
    assert response.status_code == 400


def test_trade_invalid_side_is_422(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "hold"}
    )
    assert response.status_code == 422


def test_history_after_trade(client, cache):
    cache.update("AAPL", 100.0)
    client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"}
    )
    response = client.get("/api/portfolio/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["total_value"] == DEFAULT_CASH

    assert client.get("/api/portfolio/history?limit=0").status_code == 422


def test_watchlist_read(client, cache):
    cache.update("AAPL", 190.0)
    response = client.get("/api/watchlist")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == len(DEFAULT_TICKERS)
    by_ticker = {entry["ticker"]: entry for entry in entries}
    assert by_ticker["AAPL"]["price"]["price"] == 190.0
    assert by_ticker["MSFT"]["price"] is None


def test_watchlist_add_and_duplicate(client):
    response = client.post("/api/watchlist", json={"ticker": "pypl"})
    assert response.status_code == 200
    assert response.json() == {"ticker": "PYPL", "added": True}

    response = client.post("/api/watchlist", json={"ticker": "PYPL"})
    assert response.status_code == 200
    assert response.json()["added"] is False


def test_watchlist_add_invalid_is_400(client):
    response = client.post("/api/watchlist", json={"ticker": "123"})
    assert response.status_code == 400


def test_watchlist_remove(client):
    response = client.delete("/api/watchlist/AAPL")
    assert response.status_code == 200
    assert response.json() == {"ticker": "AAPL", "removed": True}

    tickers = [entry["ticker"] for entry in client.get("/api/watchlist").json()]
    assert "AAPL" not in tickers


def test_watchlist_remove_unknown_is_404(client):
    response = client.delete("/api/watchlist/PYPL")
    assert response.status_code == 404
