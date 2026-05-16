"""CoinGecko market data provider adapter.

Fetches live cryptocurrency prices from the CoinGecko API and
normalizes responses into internal types. All CoinGecko-specific
parsing and field mapping is isolated in this module.

All HTTP calls go through ``_request()`` which provides structured
logging with latency, error classification, and rate-limit detection.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from app.providers.types import NormalizedPriceHistory, NormalizedPricePoint, NormalizedQuote

logger = logging.getLogger(__name__)

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

SYMBOL_TO_COINGECKO_ID: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}

COINGECKO_ID_TO_SYMBOL: dict[str, str] = {
    v: k for k, v in SYMBOL_TO_COINGECKO_ID.items()
}

COINGECKO_ID_TO_NAME: dict[str, str] = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
}

HTTP_TIMEOUT = 10.0


class CoinGeckoProvider:
    """CoinGecko adapter implementing MarketDataProvider Protocol.

    All CoinGecko-specific JSON parsing and field mapping lives here.
    The service layer receives only NormalizedQuote and
    NormalizedPriceHistory instances.
    """

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "coingecko"

    def supports_symbol(self, symbol: str) -> bool:
        return symbol.upper() in SYMBOL_TO_COINGECKO_ID

    def get_quotes(self, symbols: list[str]) -> list[NormalizedQuote]:
        """Fetch live prices from CoinGecko /simple/price endpoint."""
        coingecko_ids = [
            SYMBOL_TO_COINGECKO_ID[s.upper()]
            for s in symbols
            if s.upper() in SYMBOL_TO_COINGECKO_ID
        ]
        if not coingecko_ids:
            return []

        params: dict[str, str] = {
            "ids": ",".join(coingecko_ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }
        headers = self._auth_headers()

        try:
            raw = self._request("/simple/price", params=params, headers=headers)
            return self._parse_quotes(raw)
        except Exception:
            logger.warning(
                "provider=%s endpoint=/simple/price symbols=%d "
                "status=error context=get_quotes",
                self.name, len(coingecko_ids),
            )
            return []

    def get_price_history(
        self,
        symbol: str,
        days: int = 30,
    ) -> NormalizedPriceHistory | None:
        """Fetch price history from CoinGecko /coins/{id}/market_chart."""
        sym = symbol.upper()
        cg_id = SYMBOL_TO_COINGECKO_ID.get(sym)
        if cg_id is None:
            return None

        params: dict[str, str] = {
            "vs_currency": "usd",
            "days": str(days),
        }
        headers = self._auth_headers()

        try:
            raw = self._request(
                f"/coins/{cg_id}/market_chart",
                params=params,
                headers=headers,
            )
            return self._parse_price_history(sym, raw)
        except Exception:
            logger.warning(
                "provider=%s endpoint=/coins/%s/market_chart symbol=%s "
                "status=error context=get_price_history",
                self.name, cg_id, sym,
            )
            return None

    # ------------------------------------------------------------------
    # Private: HTTP and parsing (provider-specific logic)
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        if self._api_key:
            return {"x-cg-demo-api-key": self._api_key}
        return {}

    def _request(
        self,
        path: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP GET request to CoinGecko and return parsed JSON.

        Logs structured provider metrics on every call (success and
        failure). Classifies errors as ``rate_limit``, ``timeout``,
        ``http_error``, or ``parse_error``.

        Raises httpx.HTTPStatusError on non-2xx responses.
        Raises httpx.TimeoutException on timeout.
        """
        url = f"{COINGECKO_BASE_URL}{path}"
        start = time.monotonic()
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                resp = client.get(url, params=params, headers=headers)
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
                    raise ValueError("Invalid JSON from CoinGecko") from exc

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

    def _parse_quotes(self, raw: dict[str, Any]) -> list[NormalizedQuote]:
        """Parse CoinGecko /simple/price response into NormalizedQuotes.

        Expected raw format:
        {
            "bitcoin": {"usd": 67500.0, "usd_24h_change": 1.23},
            "ethereum": {"usd": 3200.0, "usd_24h_change": -0.5}
        }
        """
        now = datetime.now(tz=timezone.utc)
        quotes: list[NormalizedQuote] = []

        for cg_id, values in raw.items():
            sym = COINGECKO_ID_TO_SYMBOL.get(cg_id)
            if sym is None or "usd" not in values:
                continue

            price = float(values["usd"])
            change_pct = float(values.get("usd_24h_change", 0.0))
            change_abs = round(price * change_pct / 100.0, 2)

            quotes.append(
                NormalizedQuote(
                    symbol=sym,
                    name=COINGECKO_ID_TO_NAME.get(cg_id, sym),
                    price=price,
                    change_24h=change_abs,
                    change_24h_pct=round(change_pct, 2),
                    source="coingecko",
                    timestamp=now,
                )
            )

        return quotes

    def _parse_price_history(
        self, symbol: str, raw: dict[str, Any]
    ) -> NormalizedPriceHistory | None:
        """Parse CoinGecko /coins/{id}/market_chart response.

        Expected raw format:
        {
            "prices": [[timestamp_ms, price], ...],
            "market_caps": [...],
            "total_volumes": [...]
        }
        """
        prices_raw = raw.get("prices")
        if not prices_raw:
            return None

        points: list[NormalizedPricePoint] = []
        for entry in prices_raw:
            if len(entry) < 2:
                continue
            ts = datetime.fromtimestamp(entry[0] / 1000.0, tz=timezone.utc)
            points.append(NormalizedPricePoint(timestamp=ts, close=float(entry[1])))

        cg_id = SYMBOL_TO_COINGECKO_ID.get(symbol, "")
        return NormalizedPriceHistory(
            symbol=symbol,
            name=COINGECKO_ID_TO_NAME.get(cg_id, symbol),
            interval="1d",
            points=points,
            source="coingecko",
        )
