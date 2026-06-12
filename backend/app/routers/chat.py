"""Chat endpoint."""

from fastapi import APIRouter, HTTPException, Request

from app.api_models import ChatRequest
from app.services import chat
from app.services.llm import ChatUnavailableError

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def send_message(body: ChatRequest, request: Request) -> dict:
    """Send a message to the assistant; trades and watchlist changes auto-execute."""
    try:
        return await chat.handle_message(
            request.app.state.price_cache,
            request.app.state.market_source,
            body.message,
        )
    except ChatUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/history")
async def read_history(limit: int = 50) -> list[dict]:
    """Recent chat messages with executed actions, chronological order."""
    return chat.get_history(limit)
