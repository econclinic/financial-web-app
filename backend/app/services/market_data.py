"""Market data service.

Uses real-time CoinGecko prices for crypto (BTC, ETH).
Falls back to mock data for symbols not available on CoinGecko (e.g. AAPL).
Price history remains mock for now.
"""

import math
import random
from datetime import datetime, timedelta, timezone

from app.schemas.market_data import MarketQuote, PricePoint
from app.services.market_data_service import SYMBOL_TO_COINGECKO, get_live_prices

_SYMBOLS: dict[str, dict[str, float | str]] = {
    "BTC": {"name": "Bitcoin", "base_price": 62_450.00},
    "ETH": {"name": "Ethereum", "base_price": 3_180.00},
    "AAPL": {"name": "Apple Inc.", "base_price": 189.50},
}

random.seed(42)


def _jitter(base: float, pct: float = 0.02) -> float:
    return base * (1 + random.uniform(-pct, pct))


def get_latest_quotes() -> list[MarketQuote]:
    now = datetime.now(tz=timezone.utc)

    crypto_symbols = [s for s in _SYMBOLS if s in SYMBOL_TO_COINGECKO]
    try:
        live = get_live_prices(crypto_symbols)
    except Exception:
        live = {}

    quotes: list[MarketQuote] = []
    for symbol, info in _SYMBOLS.items():
        base = float(info["base_price"])

        if symbol in live:
            price = round(live[symbol]["price"], 2)
            change_24h = live[symbol].get("change_24h", 0.0)
            change = round(price - base, 2)
            change_pct = round(change_24h, 2)
        else:
            price = round(_jitter(base), 2)
            change = round(price - base, 2)
            change_pct = round((change / base) * 100, 2)

        quotes.append(
            MarketQuote(
                symbol=symbol,
                name=str(info["name"]),
                price=price,
                change=change,
                change_percent=change_pct,
                updated_at=now,
            )
        )
    return quotes


def get_price_history(symbol: str, days: int = 30) -> list[PricePoint] | None:
    symbol = symbol.upper()
    if symbol not in _SYMBOLS:
        return None

    base = float(_SYMBOLS[symbol]["base_price"])
    now = datetime.now(tz=timezone.utc)
    points: list[PricePoint] = []

    for i in range(days):
        t = now - timedelta(days=days - 1 - i)
        noise = math.sin(i * 0.5) * base * 0.03 + random.uniform(-base * 0.01, base * 0.01)
        price = round(base + noise, 2)
        points.append(PricePoint(timestamp=t, price=price))

    return points
