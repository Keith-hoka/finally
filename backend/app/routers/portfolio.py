"""Portfolio and trading endpoints."""

from fastapi import APIRouter, HTTPException, Query, Request

from app.api_models import TradeRequest
from app.services import portfolio
from app.services.validation import ValidationError

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("")
async def read_portfolio(request: Request) -> dict:
    """Cash balance, positions with live valuation, and total value."""
    return portfolio.get_portfolio(request.app.state.price_cache)


@router.post("/trade")
async def execute_trade(body: TradeRequest, request: Request) -> dict:
    """Execute a market order at the current price."""
    try:
        return await portfolio.execute_trade(
            request.app.state.price_cache,
            request.app.state.market_source,
            body.ticker,
            body.quantity,
            body.side,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/history")
async def read_history(limit: int = Query(default=1000, ge=1, le=10000)) -> list[dict]:
    """Portfolio value snapshots in chronological order."""
    return portfolio.get_history(limit)
