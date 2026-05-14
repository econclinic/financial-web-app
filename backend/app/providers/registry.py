"""Provider registry — routes symbols to the correct provider adapter.

Intentionally simple: no plugin system, no dynamic loading, no DI
framework. Just a lookup that maps symbols to provider instances.

Routing logic:
    crypto symbols  → CoinGecko
    stock symbols   → Finnhub
    unknown symbols → Mock (explicit fallback for demo/unsupported)
"""

from __future__ import annotations

import logging

from app.core.config import settings
from app.providers.base import MarketDataProvider
from app.providers.coingecko import CoinGeckoProvider
from app.providers.finnhub import FinnhubProvider
from app.providers.mock import MockMarketDataProvider

logger = logging.getLogger(__name__)

# Singleton provider instances (created once per process)
_coingecko = CoinGeckoProvider(api_key=settings.COINGECKO_API_KEY)
_finnhub = FinnhubProvider(api_key=settings.FINNHUB_API_KEY)
_mock = MockMarketDataProvider()

# Ordered list of real providers to check. First match wins.
_REAL_PROVIDERS: list[MarketDataProvider] = [_coingecko, _finnhub]


def get_provider(symbol: str) -> MarketDataProvider:
    """Return the provider responsible for a given symbol.

    Checks real providers in order (CoinGecko, Finnhub). If none
    support the symbol, returns the mock provider as an explicit
    fallback for demo/unsupported symbols.
    """
    sym = symbol.upper()
    for provider in _REAL_PROVIDERS:
        if provider.supports_symbol(sym):
            return provider
    return _mock


def get_mock_provider() -> MockMarketDataProvider:
    """Return the mock provider instance (for explicit mock usage)."""
    return _mock


def get_providers_for_symbols(
    symbols: list[str],
) -> dict[MarketDataProvider, list[str]]:
    """Group symbols by their responsible provider.

    Returns a dict mapping provider instances to the list of symbols
    each should handle. This allows batching API calls per provider.
    """
    groups: dict[MarketDataProvider, list[str]] = {}
    for symbol in symbols:
        provider = get_provider(symbol)
        groups.setdefault(provider, []).append(symbol.upper())
    return groups


def has_real_provider(symbol: str) -> bool:
    """Return True if the symbol has a real (non-mock) provider."""
    sym = symbol.upper()
    return any(p.supports_symbol(sym) for p in _REAL_PROVIDERS)
