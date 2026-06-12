"""Fixtures for service tests: a price cache and a fake data source."""

import pytest

from app.market import MarketDataSource, PriceCache


class FakeSource(MarketDataSource):
    """Records add/remove calls; serves a fixed price on add_ticker."""

    def __init__(self, cache: PriceCache, prices: dict[str, float] | None = None):
        self.cache = cache
        self.prices = prices or {}
        self.added: list[str] = []
        self.removed: list[str] = []

    async def start(self, tickers: list[str]) -> None:
        for ticker in tickers:
            if ticker in self.prices:
                self.cache.update(ticker, self.prices[ticker])

    async def stop(self) -> None:
        pass

    async def add_ticker(self, ticker: str) -> None:
        self.added.append(ticker)
        if ticker in self.prices:
            self.cache.update(ticker, self.prices[ticker])

    async def remove_ticker(self, ticker: str) -> None:
        self.removed.append(ticker)
        self.cache.remove(ticker)

    def get_tickers(self) -> list[str]:
        return list(self.cache.get_all())


@pytest.fixture
def cache():
    return PriceCache()


@pytest.fixture
def source(cache):
    return FakeSource(cache, prices={"PYPL": 60.0})
