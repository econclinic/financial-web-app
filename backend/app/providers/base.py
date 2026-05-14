"""Protocol definitions for market data providers.

Each provider adapter implements one or more of these Protocols.
The service layer depends only on these Protocols, never on
concrete adapter classes.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.providers.types import (
    NormalizedEconomicSeries,
    NormalizedPriceHistory,
    NormalizedQuote,
)


@runtime_checkable
class MarketDataProvider(Protocol):
    """Protocol for providers that supply asset quotes and price history."""

    @property
    def name(self) -> str:
        """Human-readable provider name (e.g. 'coingecko', 'finnhub')."""
        ...

    def get_quotes(self, symbols: list[str]) -> list[NormalizedQuote]:
        """Fetch current quotes for the given symbols.

        Returns a list of NormalizedQuote for symbols this provider
        supports. Symbols the provider does not cover are silently
        omitted from the result.
        """
        ...

    def get_price_history(
        self,
        symbol: str,
        days: int = 30,
    ) -> NormalizedPriceHistory | None:
        """Fetch historical price data for a single symbol.

        Returns None if the symbol is not supported by this provider.
        """
        ...

    def supports_symbol(self, symbol: str) -> bool:
        """Return True if this provider can supply data for the symbol."""
        ...


@runtime_checkable
class EconomicDataProvider(Protocol):
    """Protocol for providers that supply macroeconomic data series."""

    @property
    def name(self) -> str:
        """Human-readable provider name (e.g. 'fred')."""
        ...

    def get_series(
        self,
        series_id: str,
        limit: int | None = None,
    ) -> NormalizedEconomicSeries | None:
        """Fetch an economic data series by its identifier.

        Returns None if the series is not found.
        """
        ...

    def list_available_series(self) -> list[str]:
        """Return a list of series identifiers this provider supports."""
        ...
