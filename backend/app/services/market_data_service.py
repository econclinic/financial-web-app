"""Market data service layer.

Orchestrates provider adapters via the provider registry and caching.
The registry routes each symbol to the correct provider. The service
handles fallback to cached/stale data and returns data in the legacy
dict format expected by existing consumers.

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
from app.providers.coingecko import SYMBOL_TO_COINGECKO_ID
from app.providers.registry import get_providers_for_symbols
from app.providers.types import NormalizedQuote

logger = logging.getLogger(__name__)

# Backward-compatible re-export: other modules import this symbol map
SYMBOL_TO_COINGECKO: dict[str, str] = dict(SYMBOL_TO_COINGECKO_ID)

# All symbols the service layer tracks
ALL_SYMBOLS: list[str] = ["BTC", "ETH", "AAPL", "GOLD", "SILVER", "SPX"]

# Unified cache for quotes
_quotes_cache = ProviderCache(default_ttl=60.0)

CACHE_KEY_PREFIX = "quotes:"


def _quote_to_dict(q: NormalizedQuote) -> dict[str, Any]:
    """Convert a NormalizedQuote to the legacy dict format.

    Existing consumers expect: {"price": float, "change_24h": float}
    The "source" field is included so responses can be identified as
    real provider data vs mock/degraded data.
    """
    return {"price": q.price, "change_24h": q.change_24h_pct, "source": q.source}


def get_live_prices(symbols: list[str] | None = None) -> dict[str, dict[str, Any]]:
    """Return live prices for requested symbols.

    Uses the provider registry to route each symbol to the correct
    provider. Falls back to stale cache on provider failure. Symbols
    with a real provider configured never fall back to mock data.

    Returns the same dict format as before:
    {"BTC": {"price": 67500.0, "change_24h": 1.23, "source": "coingecko"}, ...}
    """
    if symbols is None:
        symbols = list(ALL_SYMBOLS)

    valid_symbols = [s.upper() for s in symbols if s.strip()]

    # Check cache first
    cache_key = CACHE_KEY_PREFIX + ",".join(sorted(valid_symbols))
    cached = _quotes_cache.get(cache_key)
    if cached is not None:
        return {s: cached[s] for s in valid_symbols if s in cached}

    # Group symbols by provider via registry
    provider_groups = get_providers_for_symbols(valid_symbols)

    result: dict[str, dict[str, Any]] = {}

    for provider, syms in provider_groups.items():
        try:
            quotes = provider.get_quotes(syms)
            for q in quotes:
                result[q.symbol] = _quote_to_dict(q)
        except Exception:
            logger.warning(
                "%s provider failed for symbols: %s", provider.name, syms
            )

    if result:
        _quotes_cache.set(cache_key, result)

    # For any symbols that failed, try stale cache
    missing = [s for s in valid_symbols if s not in result]
    if missing:
        stale = _quotes_cache.get_stale(cache_key)
        if stale:
            for s in missing:
                if s in stale:
                    result[s] = stale[s]

    if result:
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
