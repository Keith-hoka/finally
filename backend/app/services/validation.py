"""Input validation shared by trading and watchlist services."""

from __future__ import annotations

import re

TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}$")


class ValidationError(ValueError):
    """A request failed validation; the message is safe to show the user."""


def normalize_ticker(ticker: str) -> str:
    """Uppercase and validate a ticker symbol (1-5 letters)."""
    ticker = ticker.strip().upper()
    if not TICKER_PATTERN.match(ticker):
        raise ValidationError(f"Invalid ticker '{ticker}': must be 1-5 letters")
    return ticker


def normalize_quantity(quantity: float) -> float:
    """Round to 4 decimal places and require a positive value."""
    quantity = round(quantity, 4)
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than zero")
    return quantity
