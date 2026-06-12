"""FinAlly FastAPI application."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.market import PriceCache, create_market_data_source, create_stream_router
from app.routers import chat as chat_router
from app.routers import portfolio as portfolio_router
from app.routers import system as system_router
from app.routers import watchlist as watchlist_router
from app.services import portfolio as portfolio_service
from app.services import watchlist as watchlist_service

SNAPSHOT_INTERVAL_SECONDS = 30.0
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the database, start market data, and run the snapshot task."""
    init_db()
    cache: PriceCache = app.state.price_cache
    source = create_market_data_source(cache)
    app.state.market_source = source

    tickers = sorted(
        set(watchlist_service.watchlist_tickers())
        | set(portfolio_service.position_tickers())
    )
    await source.start(tickers)
    snapshot_task = asyncio.create_task(_snapshot_loop(cache))

    yield

    snapshot_task.cancel()
    await source.stop()


async def _snapshot_loop(cache: PriceCache) -> None:
    """Record a portfolio snapshot every SNAPSHOT_INTERVAL_SECONDS."""
    while True:
        await asyncio.sleep(SNAPSHOT_INTERVAL_SECONDS)
        try:
            portfolio_service.record_snapshot(cache)
        except Exception:
            logger.exception("Portfolio snapshot failed")


def create_app() -> FastAPI:
    """Build the FastAPI app with all routers and optional static frontend."""
    load_dotenv(ENV_FILE)
    app = FastAPI(title="FinAlly", lifespan=lifespan)
    app.state.price_cache = PriceCache()

    app.include_router(system_router.router)
    app.include_router(portfolio_router.router)
    app.include_router(watchlist_router.router)
    app.include_router(chat_router.router)
    app.include_router(create_stream_router(app.state.price_cache))

    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app()
