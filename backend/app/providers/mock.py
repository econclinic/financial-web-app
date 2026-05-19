"""Mock market data provider for development and fallback.

Produces deterministic fake data using seeded PRNG — suitable for
offline development, testing, and as a last-resort fallback when
real providers are unavailable.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta, timezone

from app.providers.types import NormalizedPriceHistory, NormalizedPricePoint, NormalizedQuote

_MOCK_ASSETS: dict[str, dict[str, object]] = {
    "BTC": {"name": "Bitcoin", "base_price": 62_450.00},
    "ETH": {"name": "Ethereum", "base_price": 3_180.00},
    "AAPL": {"name": "Apple Inc.", "base_price": 189.50},
    "GOLD": {"name": "Gold", "base_price": 2_340.00},
    "SILVER": {"name": "Silver", "base_price": 29.50},
    "SPX": {"name": "S&P 500", "base_price": 5_280.00},
}

_rng = random.Random(42)


class MockMarketDataProvider:
    """Mock provider implementing MarketDataProvider Protocol."""

    @property
    def name(self) -> str:
        return "mock"

    def supports_symbol(self, symbol: str) -> bool:
        return symbol.upper() in _MOCK_ASSETS

    def get_quotes(self, symbols: list[str]) -> list[NormalizedQuote]:
        now = datetime.now(tz=timezone.utc)
        quotes: list[NormalizedQuote] = []

        for symbol in symbols:
            sym = symbol.upper()
            asset = _MOCK_ASSETS.get(sym)
            if asset is None:
                continue

            base = float(asset["base_price"])  # type: ignore[arg-type]
            price = round(base * (1 + _rng.uniform(-0.02, 0.02)), 2)
            change = round(price - base, 2)
            change_pct = round((change / base) * 100, 2)

            quotes.append(
                NormalizedQuote(
                    symbol=sym,
                    name=str(asset["name"]),
                    price=price,
                    change_24h=change,
                    change_24h_pct=change_pct,
                    source="mock",
                    timestamp=now,
                )
            )

        return quotes

    def get_price_history(
        self,
        symbol: str,
        days: int = 30,
    ) -> NormalizedPriceHistory | None:
        sym = symbol.upper()
        asset = _MOCK_ASSETS.get(sym)
        if asset is None:
            return None

        base = float(asset["base_price"])  # type: ignore[arg-type]
        now = datetime.now(tz=timezone.utc)
        points: list[NormalizedPricePoint] = []

        for i in range(days):
            t = now - timedelta(days=days - 1 - i)
            noise = (
                math.sin(i * 0.5) * base * 0.03
                + _rng.uniform(-base * 0.01, base * 0.01)
            )
            price = round(base + noise, 2)
            points.append(NormalizedPricePoint(timestamp=t, close=price))

        return NormalizedPriceHistory(
            symbol=sym,
            name=str(asset["name"]),
            interval="1d",
            points=points,
            source="mock",
        )
