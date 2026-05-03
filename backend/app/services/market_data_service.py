"""Real-time market data service using CoinGecko public API.

Fetches live crypto prices with 60-second in-memory caching.
Falls back to last cached prices on API failure; returns 503 if
no cache exists.
"""

import time
from typing import Any

import httpx
from fastapi import HTTPException, status

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

SYMBOL_TO_COINGECKO: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}

COINGECKO_TO_SYMBOL: dict[str, str] = {v: k for k, v in SYMBOL_TO_COINGECKO.items()}

CACHE_TTL_SECONDS = 60

_price_cache: dict[str, dict[str, Any]] = {}
_cache_timestamp: float = 0.0


def _is_cache_fresh() -> bool:
    return time.time() - _cache_timestamp < CACHE_TTL_SECONDS


def _fetch_from_coingecko(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """Fetch live prices from CoinGecko for the given internal symbols."""
    coingecko_ids = [
        SYMBOL_TO_COINGECKO[s] for s in symbols if s in SYMBOL_TO_COINGECKO
    ]
    if not coingecko_ids:
        return {}

    ids_param = ",".join(coingecko_ids)
    params = {
        "ids": ids_param,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }

    with httpx.Client(timeout=10.0) as client:
        resp = client.get(COINGECKO_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    result: dict[str, dict[str, Any]] = {}
    for cg_id, values in data.items():
        sym = COINGECKO_TO_SYMBOL.get(cg_id)
        if sym and "usd" in values:
            result[sym] = {
                "price": values["usd"],
                "change_24h": values.get("usd_24h_change", 0.0),
            }
    return result


def get_live_prices(symbols: list[str] | None = None) -> dict[str, dict[str, Any]]:
    """Return live prices for requested symbols.

    Uses 60-second in-memory cache. On CoinGecko failure, returns stale
    cache if available; raises 503 if no cache exists.
    """
    global _price_cache, _cache_timestamp

    if symbols is None:
        symbols = list(SYMBOL_TO_COINGECKO.keys())

    valid_symbols = [s.upper() for s in symbols if s.upper() in SYMBOL_TO_COINGECKO]

    if _is_cache_fresh() and all(s in _price_cache for s in valid_symbols):
        return {s: _price_cache[s] for s in valid_symbols if s in _price_cache}

    try:
        fresh = _fetch_from_coingecko(valid_symbols)
        _price_cache.update(fresh)
        _cache_timestamp = time.time()
        return {s: _price_cache[s] for s in valid_symbols if s in _price_cache}
    except Exception:
        if _price_cache:
            return {s: _price_cache[s] for s in valid_symbols if s in _price_cache}
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Market data temporarily unavailable. Please try again later.",
        )


def get_current_prices_map(symbols: list[str] | None = None) -> dict[str, float]:
    """Convenience method returning {symbol: price} for portfolio calculations."""
    data = get_live_prices(symbols)
    return {sym: info["price"] for sym, info in data.items()}
