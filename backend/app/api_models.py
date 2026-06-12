"""Pydantic request models for the REST API."""

from typing import Literal

from pydantic import BaseModel


class TradeRequest(BaseModel):
    ticker: str
    quantity: float
    side: Literal["buy", "sell"]


class WatchlistAddRequest(BaseModel):
    ticker: str


class ChatRequest(BaseModel):
    message: str
