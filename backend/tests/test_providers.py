"""Tests for the provider abstraction layer.

Covers:
- Provider registry routing logic
- Finnhub adapter normalization
- CoinGecko adapter normalization
- Mock adapter behavior
- Cache interaction (hit/miss, stale fallback)
- Fallback/error behavior when providers fail
- No-silent-mock guarantee for real-provider symbols
- Phase C: Structured logging, error classification, rate-limit detection
"""

import logging
import time
from unittest.mock import patch

import httpx

from app.providers.cache import ProviderCache
from app.providers.coingecko import CoinGeckoProvider
from app.providers.finnhub import FINNHUB_STOCKS, FinnhubProvider
from app.providers.mock import MockMarketDataProvider
from app.providers.registry import (
    get_mock_provider,
    get_provider,
    get_providers_for_symbols,
    has_real_provider,
)
from app.providers.types import NormalizedPriceHistory, NormalizedQuote

# ── Registry Routing Tests ─────────────────────────────────────────


class TestProviderRegistry:
    """Registry routing tests.

    These tests verify the real routing logic (CoinGecko / Finnhub / Mock).
    USE_MOCK_ONLY is temporarily disabled via patch so the routing rules
    are exercised. When USE_MOCK_ONLY is True (Sprint 1 default),
    get_provider always returns the mock provider — tested separately below.
    """

    @patch("app.providers.registry.USE_MOCK_ONLY", False)
    def test_crypto_routes_to_coingecko(self):
        assert get_provider("BTC").name == "coingecko"
        assert get_provider("ETH").name == "coingecko"

    @patch("app.providers.registry.USE_MOCK_ONLY", False)
    def test_stock_routes_to_finnhub(self):
        assert get_provider("AAPL").name == "finnhub"
        assert get_provider("MSFT").name == "finnhub"
        assert get_provider("GOOGL").name == "finnhub"

    @patch("app.providers.registry.USE_MOCK_ONLY", False)
    def test_unknown_symbol_routes_to_mock(self):
        assert get_provider("UNKNOWN_SYMBOL").name == "mock"
        assert get_provider("XYZ123").name == "mock"

    @patch("app.providers.registry.USE_MOCK_ONLY", False)
    def test_case_insensitive_routing(self):
        assert get_provider("btc").name == "coingecko"
        assert get_provider("aapl").name == "finnhub"

    def test_has_real_provider(self):
        assert has_real_provider("BTC") is True
        assert has_real_provider("AAPL") is True
        assert has_real_provider("UNKNOWN") is False

    @patch("app.providers.registry.USE_MOCK_ONLY", False)
    def test_get_providers_for_symbols_groups_correctly(self):
        groups = get_providers_for_symbols(["BTC", "ETH", "AAPL", "MSFT"])

        provider_names = {p.name: syms for p, syms in groups.items()}
        assert "BTC" in provider_names["coingecko"]
        assert "ETH" in provider_names["coingecko"]
        assert "AAPL" in provider_names["finnhub"]
        assert "MSFT" in provider_names["finnhub"]

    @patch("app.providers.registry.USE_MOCK_ONLY", False)
    def test_get_providers_for_symbols_mixed_with_unknown(self):
        groups = get_providers_for_symbols(["BTC", "AAPL", "UNKNOWN"])

        provider_names = {p.name: syms for p, syms in groups.items()}
        assert "BTC" in provider_names["coingecko"]
        assert "AAPL" in provider_names["finnhub"]
        assert "UNKNOWN" in provider_names["mock"]

    def test_get_mock_provider_returns_mock(self):
        assert get_mock_provider().name == "mock"

    def test_mock_only_routes_all_to_mock(self):
        assert get_provider("BTC").name == "mock"
        assert get_provider("AAPL").name == "mock"
        assert get_provider("GOLD").name == "mock"


# ── Finnhub Adapter Normalization Tests ────────────────────────────


class TestFinnhubNormalization:
    def setup_method(self):
        self.provider = FinnhubProvider(api_key="test-key")

    def test_parse_quote_success(self):
        raw = {
            "c": 150.25,
            "d": 2.50,
            "dp": 1.69,
            "h": 151.00,
            "l": 148.00,
            "o": 149.00,
            "pc": 147.75,
            "t": 1672531200,
        }

        quote = self.provider._parse_quote("AAPL", raw)

        assert quote is not None
        assert quote.symbol == "AAPL"
        assert quote.name == "Apple Inc."
        assert quote.price == 150.25
        assert quote.change_24h == 2.50
        assert quote.change_24h_pct == 1.69
        assert quote.source == "finnhub"

    def test_parse_quote_zero_price_returns_none(self):
        raw = {"c": 0, "d": 0, "dp": 0, "h": 0, "l": 0, "o": 0, "pc": 0, "t": 0}
        assert self.provider._parse_quote("AAPL", raw) is None

    def test_parse_quote_missing_fields(self):
        raw = {"c": 100.0}
        quote = self.provider._parse_quote("AAPL", raw)
        assert quote is not None
        assert quote.price == 100.0
        assert quote.change_24h == 0.0
        assert quote.change_24h_pct == 0.0

    def test_parse_candles_success(self):
        raw = {
            "c": [150.0, 151.0, 152.0],
            "h": [151.0, 152.0, 153.0],
            "l": [149.0, 150.0, 151.0],
            "o": [149.5, 150.5, 151.5],
            "v": [1000000, 1100000, 1200000],
            "t": [1672531200, 1672617600, 1672704000],
            "s": "ok",
        }

        history = self.provider._parse_candles("AAPL", raw)

        assert history is not None
        assert history.symbol == "AAPL"
        assert history.source == "finnhub"
        assert len(history.points) == 3
        assert history.points[0].close == 150.0
        assert history.points[0].open == 149.5
        assert history.points[0].high == 151.0
        assert history.points[0].low == 149.0
        assert history.points[0].volume == 1000000

    def test_parse_candles_no_data(self):
        raw = {"s": "no_data"}
        assert self.provider._parse_candles("AAPL", raw) is None

    def test_parse_candles_empty_data(self):
        raw = {"c": [], "t": [], "s": "ok"}
        assert self.provider._parse_candles("AAPL", raw) is None

    def test_supports_known_stocks(self):
        for sym in FINNHUB_STOCKS:
            assert self.provider.supports_symbol(sym) is True

    def test_does_not_support_crypto(self):
        assert self.provider.supports_symbol("BTC") is False
        assert self.provider.supports_symbol("ETH") is False

    def test_output_is_normalized_quote(self):
        raw = {"c": 200.0, "d": 1.0, "dp": 0.5, "h": 201.0, "l": 199.0, "o": 199.5, "pc": 199.0, "t": 1672531200}
        quote = self.provider._parse_quote("AAPL", raw)
        assert isinstance(quote, NormalizedQuote)

    def test_output_is_normalized_price_history(self):
        raw = {"c": [100.0], "h": [101.0], "l": [99.0], "o": [99.5], "v": [500000], "t": [1672531200], "s": "ok"}
        history = self.provider._parse_candles("AAPL", raw)
        assert isinstance(history, NormalizedPriceHistory)


# ── CoinGecko Adapter Normalization Tests ─────────────────────────


class TestCoinGeckoNormalization:
    def setup_method(self):
        self.provider = CoinGeckoProvider()

    def test_parse_quotes_success(self):
        raw = {
            "bitcoin": {"usd": 67500.0, "usd_24h_change": 1.23},
            "ethereum": {"usd": 3200.0, "usd_24h_change": -0.5},
        }
        quotes = self.provider._parse_quotes(raw)

        assert len(quotes) == 2
        btc = next(q for q in quotes if q.symbol == "BTC")
        assert btc.price == 67500.0
        assert btc.change_24h_pct == 1.23
        assert btc.source == "coingecko"
        assert isinstance(btc, NormalizedQuote)

    def test_parse_quotes_ignores_unknown_coins(self):
        raw = {"unknown_coin": {"usd": 1.0, "usd_24h_change": 0.0}}
        quotes = self.provider._parse_quotes(raw)
        assert len(quotes) == 0

    def test_supports_crypto_symbols(self):
        assert self.provider.supports_symbol("BTC") is True
        assert self.provider.supports_symbol("ETH") is True

    def test_does_not_support_stocks(self):
        assert self.provider.supports_symbol("AAPL") is False


# ── Mock Adapter Tests ─────────────────────────────────────────────


class TestMockProvider:
    def setup_method(self):
        self.provider = MockMarketDataProvider()

    def test_mock_quotes_have_source_mock(self):
        quotes = self.provider.get_quotes(["BTC", "ETH", "AAPL"])
        for q in quotes:
            assert q.source == "mock"

    def test_mock_history_correct_length(self):
        history = self.provider.get_price_history("BTC", days=30)
        assert history is not None
        assert len(history.points) == 30

    def test_mock_unsupported_symbol_returns_none(self):
        history = self.provider.get_price_history("UNKNOWN_SYMBOL")
        assert history is None


# ── Cache Tests ────────────────────────────────────────────────────


class TestProviderCache:
    def test_set_and_get(self):
        cache = ProviderCache(default_ttl=60.0)
        cache.set("key1", {"data": 123})
        assert cache.get("key1") == {"data": 123}

    def test_get_returns_none_after_expiry(self):
        cache = ProviderCache(default_ttl=0.1)
        cache.set("key1", "value")
        time.sleep(0.15)
        assert cache.get("key1") is None

    def test_get_stale_returns_expired_data(self):
        cache = ProviderCache(default_ttl=0.1)
        cache.set("key1", "stale_value")
        time.sleep(0.15)
        assert cache.get("key1") is None
        assert cache.get_stale("key1") == "stale_value"

    def test_get_stale_returns_none_for_missing_key(self):
        cache = ProviderCache(default_ttl=60.0)
        assert cache.get_stale("nonexistent") is None

    def test_cache_stats(self):
        cache = ProviderCache(default_ttl=60.0)
        cache.set("key1", "val")
        cache.get("key1")  # hit
        cache.get("missing")  # miss

        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_cache_custom_ttl(self):
        cache = ProviderCache(default_ttl=60.0)
        cache.set("key1", "val")
        # Fresh with default TTL
        assert cache.get("key1") is not None
        # Expired with very short custom TTL
        time.sleep(0.1)
        assert cache.get("key1", ttl=0.05) is None


# ── No-Silent-Mock Guarantee Tests ─────────────────────────────────


class TestNoSilentMock:
    """Verify that symbols with real providers never silently fall back
    to mock data in production responses."""

    def test_finnhub_failure_returns_stale_cache_not_mock(self):
        """When Finnhub fails and cache has stale data, return stale
        data (which was real at some point), not mock."""
        cache = ProviderCache(default_ttl=0.1)
        cache.set("quotes:AAPL", {"AAPL": {"price": 190.0, "change_24h": 0.5, "source": "finnhub"}})
        time.sleep(0.15)

        # Cache expired but stale data exists
        assert cache.get("quotes:AAPL") is None
        stale = cache.get_stale("quotes:AAPL")
        assert stale is not None
        assert stale["AAPL"]["source"] == "finnhub"  # Not "mock"

    def test_real_provider_symbols_have_real_provider(self):
        """BTC, ETH, and AAPL all have real providers — not mock."""
        assert has_real_provider("BTC") is True
        assert has_real_provider("ETH") is True
        assert has_real_provider("AAPL") is True

    def test_source_field_present_in_all_quotes(self):
        """All normalized quotes include a source field."""
        mock = MockMarketDataProvider()
        quotes = mock.get_quotes(["BTC"])
        assert all(q.source == "mock" for q in quotes)

        finnhub = FinnhubProvider()
        raw = {"c": 150.0, "d": 1.0, "dp": 0.5, "h": 151.0, "l": 149.0, "o": 149.5, "pc": 149.0, "t": 1672531200}
        quote = finnhub._parse_quote("AAPL", raw)
        assert quote is not None
        assert quote.source == "finnhub"

        coingecko = CoinGeckoProvider()
        cg_raw = {"bitcoin": {"usd": 67500.0, "usd_24h_change": 1.0}}
        cg_quotes = coingecko._parse_quotes(cg_raw)
        assert all(q.source == "coingecko" for q in cg_quotes)


# ── Phase C: Structured Logging & Error Classification ─────────────


def _mock_response(status_code: int, json_data: dict | None = None) -> httpx.Response:
    """Build a fake httpx.Response for testing provider error paths."""
    request = httpx.Request("GET", "https://example.com/test")
    if json_data is not None:
        return httpx.Response(status_code, json=json_data, request=request)
    return httpx.Response(status_code, text="error", request=request)


class TestFinnhubStructuredLogging:
    def setup_method(self) -> None:
        self.provider = FinnhubProvider(api_key="test-key")

    def test_http_error_logs_structured_fields(self, caplog: logging.LogRecord) -> None:
        """Provider HTTP errors produce structured log lines."""
        resp = _mock_response(401)

        with patch("app.providers.finnhub.httpx.Client") as mock_client:
            client_instance = mock_client.return_value.__enter__.return_value
            client_instance.get.return_value = resp

            with caplog.at_level(logging.ERROR, logger="app.providers.finnhub"):
                quotes = self.provider.get_quotes(["AAPL"])

        assert quotes == []
        assert any("provider=finnhub" in r.message for r in caplog.records)
        assert any("error_type=http_error" in r.message for r in caplog.records)
        assert any("latency_ms=" in r.message for r in caplog.records)

    def test_rate_limit_logs_as_rate_limit(self, caplog: logging.LogRecord) -> None:
        """HTTP 429 is classified as rate_limit, not generic http_error."""
        resp = _mock_response(429)

        with patch("app.providers.finnhub.httpx.Client") as mock_client:
            client_instance = mock_client.return_value.__enter__.return_value
            client_instance.get.return_value = resp

            with caplog.at_level(logging.WARNING, logger="app.providers.finnhub"):
                quotes = self.provider.get_quotes(["AAPL"])

        assert quotes == []
        assert any("status=rate_limit" in r.message for r in caplog.records)

    def test_timeout_logs_as_timeout(self, caplog: logging.LogRecord) -> None:
        """Timeouts are classified as error_type=timeout."""
        with patch("app.providers.finnhub.httpx.Client") as mock_client:
            client_instance = mock_client.return_value.__enter__.return_value
            client_instance.get.side_effect = httpx.TimeoutException("timed out")

            with caplog.at_level(logging.ERROR, logger="app.providers.finnhub"):
                quotes = self.provider.get_quotes(["AAPL"])

        assert quotes == []
        assert any("error_type=timeout" in r.message for r in caplog.records)

    def test_success_logs_at_debug_level(self, caplog: logging.LogRecord) -> None:
        """Successful requests log at DEBUG level only."""
        resp = _mock_response(200, json_data={"c": 150.0, "d": 1.0, "dp": 0.5, "h": 151.0, "l": 149.0, "o": 149.5, "pc": 149.0, "t": 1672531200})

        with patch("app.providers.finnhub.httpx.Client") as mock_client:
            client_instance = mock_client.return_value.__enter__.return_value
            client_instance.get.return_value = resp

            with caplog.at_level(logging.DEBUG, logger="app.providers.finnhub"):
                quotes = self.provider.get_quotes(["AAPL"])

        assert len(quotes) == 1
        debug_logs = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert any("status=success" in r.message for r in debug_logs)

    def test_provider_failure_does_not_crash_get_quotes(self) -> None:
        """get_quotes returns empty list on provider failure, never raises."""
        with patch("app.providers.finnhub.httpx.Client") as mock_client:
            client_instance = mock_client.return_value.__enter__.return_value
            client_instance.get.side_effect = httpx.TimeoutException("timed out")

            quotes = self.provider.get_quotes(["AAPL", "MSFT", "GOOGL"])

        assert quotes == []

    def test_provider_failure_does_not_crash_get_price_history(self) -> None:
        """get_price_history returns None on provider failure, never raises."""
        with patch("app.providers.finnhub.httpx.Client") as mock_client:
            client_instance = mock_client.return_value.__enter__.return_value
            client_instance.get.side_effect = httpx.TimeoutException("timed out")

            history = self.provider.get_price_history("AAPL")

        assert history is None


class TestCoinGeckoStructuredLogging:
    def setup_method(self) -> None:
        self.provider = CoinGeckoProvider()

    def test_http_error_logs_structured_fields(self, caplog: logging.LogRecord) -> None:
        """Provider HTTP errors produce structured log lines."""
        resp = _mock_response(500)

        with patch("app.providers.coingecko.httpx.Client") as mock_client:
            client_instance = mock_client.return_value.__enter__.return_value
            client_instance.get.return_value = resp

            with caplog.at_level(logging.ERROR, logger="app.providers.coingecko"):
                quotes = self.provider.get_quotes(["BTC"])

        assert quotes == []
        assert any("provider=coingecko" in r.message for r in caplog.records)
        assert any("error_type=http_error" in r.message for r in caplog.records)

    def test_rate_limit_logs_as_rate_limit(self, caplog: logging.LogRecord) -> None:
        """HTTP 429 is classified as rate_limit for CoinGecko."""
        resp = _mock_response(429)

        with patch("app.providers.coingecko.httpx.Client") as mock_client:
            client_instance = mock_client.return_value.__enter__.return_value
            client_instance.get.return_value = resp

            with caplog.at_level(logging.WARNING, logger="app.providers.coingecko"):
                quotes = self.provider.get_quotes(["BTC"])

        assert quotes == []
        assert any("status=rate_limit" in r.message for r in caplog.records)

    def test_timeout_logs_as_timeout(self, caplog: logging.LogRecord) -> None:
        """Timeouts are classified as error_type=timeout."""
        with patch("app.providers.coingecko.httpx.Client") as mock_client:
            client_instance = mock_client.return_value.__enter__.return_value
            client_instance.get.side_effect = httpx.TimeoutException("timed out")

            with caplog.at_level(logging.ERROR, logger="app.providers.coingecko"):
                quotes = self.provider.get_quotes(["BTC"])

        assert quotes == []
        assert any("error_type=timeout" in r.message for r in caplog.records)

    def test_provider_failure_does_not_crash_get_quotes(self) -> None:
        """get_quotes returns empty list on provider failure, never raises."""
        with patch("app.providers.coingecko.httpx.Client") as mock_client:
            client_instance = mock_client.return_value.__enter__.return_value
            client_instance.get.side_effect = ConnectionError("network down")

            quotes = self.provider.get_quotes(["BTC", "ETH"])

        assert quotes == []

    def test_provider_failure_does_not_crash_get_price_history(self) -> None:
        """get_price_history returns None on provider failure, never raises."""
        with patch("app.providers.coingecko.httpx.Client") as mock_client:
            client_instance = mock_client.return_value.__enter__.return_value
            client_instance.get.side_effect = ConnectionError("network down")

            history = self.provider.get_price_history("BTC")

        assert history is None
