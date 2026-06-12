"""Fixtures for router tests: a TestClient over a bare app with fake state."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.market import PriceCache
from app.routers import chat, portfolio, system, watchlist
from tests.services.conftest import FakeSource


@pytest.fixture
def cache():
    return PriceCache()


@pytest.fixture
def source(cache):
    return FakeSource(cache, prices={"PYPL": 60.0})


@pytest.fixture
def client(temp_db, cache, source):
    """TestClient with routers mounted and state injected, no lifespan."""
    app = FastAPI()
    app.state.price_cache = cache
    app.state.market_source = source
    app.include_router(system.router)
    app.include_router(portfolio.router)
    app.include_router(watchlist.router)
    app.include_router(chat.router)
    return TestClient(app)
