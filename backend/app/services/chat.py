"""Chat orchestration: context building, LLM call, action execution, persistence."""

from __future__ import annotations

import json
import uuid

from app.db import DEFAULT_USER_ID, get_connection
from app.db.seed import utc_now_iso
from app.market import MarketDataSource, PriceCache

from . import portfolio as portfolio_service
from . import watchlist as watchlist_service
from .llm import AssistantReply, get_reply
from .validation import ValidationError, normalize_ticker

HISTORY_LIMIT = 20

SYSTEM_PROMPT = """\
You are FinAlly, an AI trading assistant embedded in a simulated trading workstation.
The user trades a virtual portfolio with fake money; trades fill instantly at the
current price with no fees.

Your job:
- Analyze portfolio composition, risk concentration, and P&L.
- Suggest trades with clear, data-driven reasoning.
- Execute trades when the user asks or agrees, by listing them in `trades`.
- Manage the watchlist proactively via `watchlist_changes`.
- Be concise. Use the live data below; do not invent prices.

Trades and watchlist changes you return are executed automatically. If an action
fails validation, the error will appear in the next turn's context.

Current portfolio state:
{context}
"""


async def handle_message(
    cache: PriceCache, source: MarketDataSource, user_message: str
) -> dict:
    """Run one chat turn: call the LLM, execute its actions, persist, respond."""
    history = [
        {"role": entry["role"], "content": entry["content"]}
        for entry in get_history(HISTORY_LIMIT)
    ]
    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT.format(context=_build_context(cache))}]
        + history
        + [{"role": "user", "content": user_message}]
    )
    reply = await get_reply(messages)
    actions = await _execute_actions(cache, source, reply)
    _persist_turn(user_message, reply.message, actions)
    return {"message": reply.message, "actions": actions}


def get_history(limit: int = HISTORY_LIMIT) -> list[dict]:
    """Most recent chat messages in chronological order, with actions and timestamps."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT role, content, actions, created_at FROM chat_messages
               WHERE user_id = ? ORDER BY created_at DESC, rowid DESC LIMIT ?""",
            (DEFAULT_USER_ID, limit),
        ).fetchall()
    return [
        {
            "role": row["role"],
            "content": row["content"],
            "actions": json.loads(row["actions"]) if row["actions"] else None,
            "created_at": row["created_at"],
        }
        for row in reversed(rows)
    ]


def _build_context(cache: PriceCache) -> str:
    """Portfolio, watchlist, and prices as JSON for the system prompt."""
    snapshot = portfolio_service.get_portfolio(cache)
    snapshot["watchlist"] = watchlist_service.get_watchlist(cache)
    return json.dumps(snapshot, indent=2)


async def _execute_actions(
    cache: PriceCache, source: MarketDataSource, reply: AssistantReply
) -> dict:
    """Auto-execute the reply's trades and watchlist changes, collecting errors."""
    actions: dict = {"trades": [], "watchlist_changes": [], "errors": []}

    for trade in reply.trades:
        try:
            result = await portfolio_service.execute_trade(
                cache, source, trade.ticker, trade.quantity, trade.side
            )
            actions["trades"].append(result)
        except ValidationError as exc:
            actions["errors"].append(str(exc))

    for change in reply.watchlist_changes:
        try:
            ticker = normalize_ticker(change.ticker)
            if change.action == "add":
                await watchlist_service.add_ticker(source, ticker)
            else:
                await watchlist_service.remove_ticker(source, ticker)
            actions["watchlist_changes"].append({"ticker": ticker, "action": change.action})
        except (ValidationError, watchlist_service.NotWatchedError) as exc:
            actions["errors"].append(str(exc))

    return actions


def _persist_turn(user_message: str, assistant_message: str, actions: dict) -> None:
    """Append the user and assistant messages to chat history."""
    now = utc_now_iso()
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO chat_messages (id, user_id, role, content, actions, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (str(uuid.uuid4()), DEFAULT_USER_ID, "user", user_message, None, now),
                (
                    str(uuid.uuid4()),
                    DEFAULT_USER_ID,
                    "assistant",
                    assistant_message,
                    json.dumps(actions),
                    now,
                ),
            ],
        )
