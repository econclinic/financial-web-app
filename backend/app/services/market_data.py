"""Market data service.

Uses the provider registry for live data:
- CoinGecko for crypto (BTC, ETH)
- Finnhub for stocks (AAPL)
- Mock provider for commodities/indices (GOLD, SILVER, SPX) and fallback

Price history currently uses the mock provider for all symbols.
Real price history (CoinGecko market_chart, Finnhub candles) can be
routed through the registry in a future phase once API keys are
provisioned.

This module preserves the existing public interface:
- get_latest_quotes() -> list[MarketQuote]
- get_price_history(symbol, days) -> list[PricePoint] | None
"""

from app.providers.registry import get_mock_provider
from app.schemas.market_data import MarketQuote, PricePoint
from app.services.market_data_service import get_live_prices

_SYMBOLS: dict[str, dict[str, float | str]] = {
    "BTC": {"name": "Bitcoin", "base_price": 62_450.00},
    "ETH": {"name": "Ethereum", "base_price": 3_180.00},
    "AAPL": {"name": "Apple Inc.", "base_price": 189.50},
    "GOLD": {"name": "Gold", "base_price": 2_340.00},
    "SILVER": {"name": "Silver", "base_price": 29.50},
    "SPX": {"name": "S&P 500", "base_price": 5_280.00},
}


def get_latest_quotes() -> list[MarketQuote]:
    """Return current quotes for all tracked symbols.

    Uses get_live_prices which routes through the provider registry.
    """
    from datetime import datetime, timezone

    now = datetime.now(tz=timezone.utc)

    try:
        live = get_live_prices(list(_SYMBOLS.keys()))
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
            continue

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
    """Return price history for a symbol.

    Currently uses mock provider for all price history. Real history
    (CoinGecko market_chart, Finnhub candles) will be routed through
    the provider registry once API keys are provisioned.
    """
    sym = symbol.upper()
    if sym not in _SYMBOLS:
        return None

    mock = get_mock_provider()
    history = mock.get_price_history(sym, days)
    if history is None:
        return None

    return [
        PricePoint(timestamp=p.timestamp, price=p.close) for p in history.points
    ]
