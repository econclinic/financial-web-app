"""Normalized internal data types for market data.

All provider adapters produce these types. The service layer and API
layer work exclusively with these types — never with raw provider
payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class NormalizedQuote:
    """A single asset quote, normalized across all providers."""

    symbol: str
    name: str
    price: float
    change_24h: float
    change_24h_pct: float
    volume_24h: float | None = None
    market_cap: float | None = None
    source: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=None))


@dataclass(frozen=True)
class NormalizedPricePoint:
    """A single OHLCV price point."""

    timestamp: datetime
    close: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: float | None = None


@dataclass(frozen=True)
class NormalizedPriceHistory:
    """Historical price data for a symbol."""

    symbol: str
    name: str
    interval: str  # "1d", "1h", "5m", etc.
    points: list[NormalizedPricePoint] = field(default_factory=list)
    source: str = ""


@dataclass(frozen=True)
class NormalizedEconomicObservation:
    """A single observation in an economic data series."""

    date: date
    value: float | None = None


@dataclass(frozen=True)
class NormalizedEconomicSeries:
    """An economic data series (e.g., GDP, CPI)."""

    series_id: str
    name: str
    unit: str
    frequency: str  # "monthly", "quarterly", "annual"
    observations: list[NormalizedEconomicObservation] = field(default_factory=list)
    source: str = ""
