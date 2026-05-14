"""Market data service.

Uses provider adapters for live data:
- CoinGecko for crypto (BTC, ETH)
- Mock provider for symbols not available on any real provider (e.g. AAPL)

This module preserves the existing public interface:
- get_latest_quotes() -> list[MarketQuote]
- get_price_history(symbol, days) -> list[PricePoint] | None
"""

from app.providers.mock import MockMarketDataProvider
from app.schemas.market_data import MarketQuote, PricePoint
from app.services.market_data_service import SYMBOL_TO_COINGECKO, get_live_prices

_SYMBOLS: dict[str, dict[str, float | str]] = {
    "BTC": {"name": "Bitcoin", "base_price": 62_450.00},
    "ETH": {"name": "Ethereum", "base_price": 3_180.00},
    "AAPL": {"name": "Apple Inc.", "base_price": 189.50},
}

_mock_provider = MockMarketDataProvider()


def get_latest_quotes() -> list[MarketQuote]:
    """Return current quotes for all tracked symbols.

    Uses CoinGecko for crypto symbols, mock provider for others.
    """
    from datetime import datetime, timezone

    now = datetime.now(tz=timezone.utc)

    # Fetch crypto prices via the service layer (uses CoinGecko adapter)
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
            # Use mock provider for non-crypto symbols
            mock_quotes = _mock_provider.get_quotes([symbol])
            if mock_quotes:
                mq = mock_quotes[0]
                price = round(mq.price, 2)
                change = round(mq.change_24h, 2)
                change_pct = round(mq.change_24h_pct, 2)
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

    Uses mock provider for price history (real history integration
    is planned for Phase B+).
    """
    sym = symbol.upper()
    if sym not in _SYMBOLS:
        return None

    history = _mock_provider.get_price_history(sym, days)
    if history is None:
        return None

    return [
        PricePoint(timestamp=p.timestamp, price=p.close) for p in history.points
    ]
