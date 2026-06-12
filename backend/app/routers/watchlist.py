"""Watchlist endpoints."""

from fastapi import APIRouter, HTTPException, Request

from app.api_models import WatchlistAddRequest
from app.services import watchlist
from app.services.validation import ValidationError

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("")
async def read_watchlist(request: Request) -> list[dict]:
    """Watched tickers with their latest cached prices."""
    return watchlist.get_watchlist(request.app.state.price_cache)


@router.post("")
async def add_ticker(body: WatchlistAddRequest, request: Request) -> dict:
    """Add a ticker to the watchlist. Duplicate adds are no-op successes."""
    try:
        return await watchlist.add_ticker(request.app.state.market_source, body.ticker)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{ticker}")
async def remove_ticker(ticker: str, request: Request) -> dict:
    """Remove a ticker from the watchlist."""
    try:
        await watchlist.remove_ticker(request.app.state.market_source, ticker)
    except watchlist.NotWatchedError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ticker": ticker.upper(), "removed": True}
