"""Market data service layer.

Orchestrates provider adapters and caching. Selects the appropriate
provider for each symbol, handles fallback to cached/stale data,
and returns data in the legacy dict format expected by existing consumers.

This module preserves the existing public interface:
- get_live_prices(symbols) -> dict[str, dict[str, Any]]
- get_current_prices_map(symbols) -> dict[str, float]
- SYMBOL_TO_COINGECKO (re-exported for backward compatibility)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, status

from app.providers.cache import ProviderCache
from app.providers.coingecko import SYMBOL_TO_COINGECKO_ID, CoinGeckoProvider
from app.providers.mock import MockMarketDataProvider
from app.providers.types import NormalizedQuote

logger = logging.getLogger(__name__)

# Backward-compatible re-export: other modules import this symbol map
SYMBOL_TO_COINGECKO: dict[str, str] = dict(SYMBOL_TO_COINGECKO_ID)

# Provider instances (singleton per process)
_crypto_provider = CoinGeckoProvider()
_mock_provider = MockMarketDataProvider()

# Unified cache for quotes (replaces the old module-level dict)
_quotes_cache = ProviderCache(default_ttl=60.0)

CACHE_KEY_PREFIX = "quotes:"


def _quote_to_dict(q: NormalizedQuote) -> dict[str, Any]:
    """Convert a NormalizedQuote to the legacy dict format.

    Existing consumers expect: {"price": float, "change_24h": float}
    """
    return {"price": q.price, "change_24h": q.change_24h_pct}


def get_live_prices(symbols: list[str] | None = None) -> dict[str, dict[str, Any]]:
    """Return live prices for requested symbols.

    Uses provider adapters with 60-second caching. Falls back to stale
    cache or mock data on provider failure; raises 503 if nothing is
    available.

    Returns the same dict format as before:
    {"BTC": {"price": 67500.0, "change_24h": 1.23}, ...}
    """
    if symbols is None:
        symbols = list(SYMBOL_TO_COINGECKO.keys())

    valid_symbols = [s.upper() for s in symbols if s.strip()]

    # Check cache first
    cache_key = CACHE_KEY_PREFIX + ",".join(sorted(valid_symbols))
    cached = _quotes_cache.get(cache_key)
    if cached is not None:
        return {s: cached[s] for s in valid_symbols if s in cached}

    # Separate symbols by provider
    crypto_symbols = [s for s in valid_symbols if _crypto_provider.supports_symbol(s)]

    # Fetch from CoinGecko provider
    result: dict[str, dict[str, Any]] = {}
    try:
        if crypto_symbols:
            quotes = _crypto_provider.get_quotes(crypto_symbols)
            for q in quotes:
                result[q.symbol] = _quote_to_dict(q)
    except Exception:
        logger.warning("CoinGecko provider failed, falling back to cache/mock")
        # Try stale cache
        stale = _quotes_cache.get_stale(cache_key)
        if stale:
            return {s: stale[s] for s in valid_symbols if s in stale}

        # Last resort: mock provider
        try:
            mock_quotes = _mock_provider.get_quotes(crypto_symbols)
            for q in mock_quotes:
                result[q.symbol] = _quote_to_dict(q)
        except Exception:
            pass

    if result:
        # Update cache with fresh data
        _quotes_cache.set(cache_key, result)
        return {s: result[s] for s in valid_symbols if s in result}

    # Nothing available at all
    stale = _quotes_cache.get_stale(cache_key)
    if stale:
        return {s: stale[s] for s in valid_symbols if s in stale}

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Market data temporarily unavailable. Please try again later.",
    )


def get_current_prices_map(symbols: list[str] | None = None) -> dict[str, float]:
    """Convenience method returning {symbol: price} for portfolio calculations."""
    data = get_live_prices(symbols)
    return {sym: info["price"] for sym, info in data.items()}
