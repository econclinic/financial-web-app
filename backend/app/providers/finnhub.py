"""Finnhub market data provider adapter.

Fetches live stock quotes and price history from the Finnhub REST API
and normalizes responses into internal types. All Finnhub-specific
parsing and field mapping is isolated in this module.

Finnhub API docs: https://finnhub.io/docs/api
Free tier: 60 calls/min, real-time US stock quotes.

All HTTP calls go through ``_request()`` which provides structured
logging with latency, error classification, and rate-limit detection.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from app.providers.types import (
    NormalizedPriceHistory,
    NormalizedPricePoint,
    NormalizedQuote,
)

logger = logging.getLogger(__name__)

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# Symbols this adapter supports. Expand as needed.
FINNHUB_STOCKS: dict[str, str] = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla Inc.",
    "META": "Meta Platforms Inc.",
    "NVDA": "NVIDIA Corporation",
}

HTTP_TIMEOUT = 10.0


class FinnhubProvider:
    """Finnhub adapter implementing MarketDataProvider Protocol.

    All Finnhub-specific JSON parsing and field mapping lives here.
    The service layer receives only NormalizedQuote and
    NormalizedPriceHistory instances.
    """

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "finnhub"

    def supports_symbol(self, symbol: str) -> bool:
        return symbol.upper() in FINNHUB_STOCKS

    def get_quotes(self, symbols: list[str]) -> list[NormalizedQuote]:
        """Fetch live quotes from Finnhub /quote endpoint.

        Finnhub requires one API call per symbol (no batch endpoint
        on the free tier).
        """
        quotes: list[NormalizedQuote] = []
        for symbol in symbols:
            sym = symbol.upper()
            if sym not in FINNHUB_STOCKS:
                continue
            try:
                raw = self._request("/quote", params={"symbol": sym})
                quote = self._parse_quote(sym, raw)
                if quote is not None:
                    quotes.append(quote)
            except Exception:
                logger.warning(
                    "provider=%s endpoint=/quote symbol=%s "
                    "status=error context=get_quotes",
                    self.name, sym,
                )
        return quotes

    def get_price_history(
        self,
        symbol: str,
        days: int = 30,
    ) -> NormalizedPriceHistory | None:
        """Fetch price history from Finnhub /stock/candle endpoint."""
        sym = symbol.upper()
        if sym not in FINNHUB_STOCKS:
            return None

        now = int(time.time())
        from_ts = now - (days * 86400)

        params: dict[str, str] = {
            "symbol": sym,
            "resolution": "D",
            "from": str(from_ts),
            "to": str(now),
        }

        try:
            raw = self._request("/stock/candle", params=params)
            return self._parse_candles(sym, raw)
        except Exception:
            logger.warning(
                "provider=%s endpoint=/stock/candle symbol=%s "
                "status=error context=get_price_history",
                self.name, sym,
            )
            return None

    # ------------------------------------------------------------------
    # Private: HTTP and parsing (provider-specific logic)
    # ------------------------------------------------------------------

    def _request(
        self,
        path: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP GET request to Finnhub and return parsed JSON.

        Logs structured provider metrics on every call (success and
        failure). Classifies errors as ``rate_limit``, ``timeout``,
        ``http_error``, or ``parse_error``.

        Raises httpx.HTTPStatusError on non-2xx responses.
        Raises httpx.TimeoutException on timeout.
        """
        url = f"{FINNHUB_BASE_URL}{path}"
        request_params = dict(params or {})
        if self._api_key:
            request_params["token"] = self._api_key

        start = time.monotonic()
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                resp = client.get(url, params=request_params)
                latency_ms = round((time.monotonic() - start) * 1000)

                if resp.status_code == 429:
                    logger.warning(
                        "provider=%s endpoint=%s status=rate_limit latency_ms=%d",
                        self.name, path, latency_ms,
                    )
                    resp.raise_for_status()

                resp.raise_for_status()

                try:
                    result: dict[str, Any] = resp.json()
                except Exception as exc:
                    logger.error(
                        "provider=%s endpoint=%s status=error "
                        "error_type=parse_error latency_ms=%d",
                        self.name, path, latency_ms,
                    )
                    raise ValueError("Invalid JSON from Finnhub") from exc

                logger.debug(
                    "provider=%s endpoint=%s status=success latency_ms=%d",
                    self.name, path, latency_ms,
                )
                return result

        except httpx.TimeoutException:
            latency_ms = round((time.monotonic() - start) * 1000)
            logger.error(
                "provider=%s endpoint=%s status=error "
                "error_type=timeout latency_ms=%d",
                self.name, path, latency_ms,
            )
            raise

        except httpx.HTTPStatusError as exc:
            latency_ms = round((time.monotonic() - start) * 1000)
            error_type = (
                "rate_limit" if exc.response.status_code == 429 else "http_error"
            )
            logger.error(
                "provider=%s endpoint=%s status=error "
                "error_type=%s http_status=%d latency_ms=%d",
                self.name, path, error_type,
                exc.response.status_code, latency_ms,
            )
            raise

    def _parse_quote(
        self, symbol: str, raw: dict[str, Any]
    ) -> NormalizedQuote | None:
        """Parse Finnhub /quote response into a NormalizedQuote.

        Expected raw format:
        {
            "c": 150.0,    # current price
            "d": 2.5,      # change (absolute)
            "dp": 1.69,    # change percent
            "h": 151.0,    # high of day
            "l": 148.0,    # low of day
            "o": 149.0,    # open
            "pc": 147.5,   # previous close
            "t": 1672531200  # timestamp (unix)
        }
        """
        price = raw.get("c", 0.0)
        if not price or price == 0:
            logger.warning("Finnhub returned zero price for %s", symbol)
            return None

        change_abs = float(raw.get("d") or 0.0)
        change_pct = float(raw.get("dp") or 0.0)
        ts = raw.get("t", 0)
        timestamp = (
            datetime.fromtimestamp(ts, tz=timezone.utc)
            if ts
            else datetime.now(tz=timezone.utc)
        )

        return NormalizedQuote(
            symbol=symbol,
            name=FINNHUB_STOCKS.get(symbol, symbol),
            price=float(price),
            change_24h=round(change_abs, 2),
            change_24h_pct=round(change_pct, 2),
            source="finnhub",
            timestamp=timestamp,
        )

    def _parse_candles(
        self, symbol: str, raw: dict[str, Any]
    ) -> NormalizedPriceHistory | None:
        """Parse Finnhub /stock/candle response into NormalizedPriceHistory.

        Expected raw format:
        {
            "c": [close1, close2, ...],
            "h": [high1, high2, ...],
            "l": [low1, low2, ...],
            "o": [open1, open2, ...],
            "v": [vol1, vol2, ...],
            "t": [ts1, ts2, ...],
            "s": "ok"
        }

        Returns None if status is "no_data" or data is missing.
        """
        if raw.get("s") != "ok":
            logger.info("Finnhub candles: no data for %s", symbol)
            return None

        closes = raw.get("c", [])
        highs = raw.get("h", [])
        lows = raw.get("l", [])
        opens = raw.get("o", [])
        volumes = raw.get("v", [])
        timestamps = raw.get("t", [])

        if not closes or not timestamps:
            return None

        points: list[NormalizedPricePoint] = []
        for i, ts in enumerate(timestamps):
            points.append(
                NormalizedPricePoint(
                    timestamp=datetime.fromtimestamp(ts, tz=timezone.utc),
                    close=float(closes[i]),
                    open=float(opens[i]) if i < len(opens) else None,
                    high=float(highs[i]) if i < len(highs) else None,
                    low=float(lows[i]) if i < len(lows) else None,
                    volume=float(volumes[i]) if i < len(volumes) else None,
                )
            )

        return NormalizedPriceHistory(
            symbol=symbol,
            name=FINNHUB_STOCKS.get(symbol, symbol),
            interval="1d",
            points=points,
            source="finnhub",
        )
