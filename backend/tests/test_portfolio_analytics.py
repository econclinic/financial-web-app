"""Tests for the Phase D Portfolio Analytics Engine.

Covers:
- metrics.py: position value, portfolio value, cost, PnL, return %
- allocation.py: allocation weights, largest position, asset count
- portfolio_analytics.py: orchestrator with mocked DB + market_data_service
- Edge cases: empty portfolio, single asset, missing prices, mixed asset types
"""

from unittest.mock import MagicMock, patch

from app.services.analytics.allocation import (
    asset_count,
    calculate_allocation,
    largest_position_weight,
)
from app.services.analytics.metrics import (
    PortfolioPosition,
    calculate_portfolio_value,
    calculate_position_value,
    calculate_return_pct,
    calculate_total_cost,
    calculate_total_pnl,
)
from app.services.analytics.portfolio_analytics import (
    _normalize_positions,
    get_portfolio_analytics,
)

# ── Metrics: Pure Calculation Tests ─────────────────────────────────


class TestPositionValue:
    def test_basic(self):
        assert calculate_position_value(10, 150.0) == 1500.0

    def test_fractional(self):
        assert calculate_position_value(0.5, 60000.0) == 30000.0

    def test_zero_quantity(self):
        assert calculate_position_value(0, 100.0) == 0.0


class TestPortfolioValue:
    def test_multiple_positions(self):
        positions = [
            PortfolioPosition("BTC", "crypto", 0.5, 50000.0),
            PortfolioPosition("AAPL", "equity", 10, 150.0),
        ]
        prices = {"BTC": 60000.0, "AAPL": 170.0}
        assert calculate_portfolio_value(positions, prices) == 31700.0

    def test_missing_price_excluded(self):
        positions = [
            PortfolioPosition("BTC", "crypto", 1.0, 50000.0),
            PortfolioPosition("AAPL", "equity", 10, 150.0),
        ]
        prices = {"BTC": 60000.0}
        assert calculate_portfolio_value(positions, prices) == 60000.0

    def test_empty_positions(self):
        assert calculate_portfolio_value([], {}) == 0.0


class TestTotalCost:
    def test_multiple_positions(self):
        positions = [
            PortfolioPosition("BTC", "crypto", 0.5, 50000.0),
            PortfolioPosition("AAPL", "equity", 10, 150.0),
        ]
        assert calculate_total_cost(positions) == 26500.0

    def test_empty(self):
        assert calculate_total_cost([]) == 0.0


class TestPnl:
    def test_profit(self):
        assert calculate_total_pnl(12000.0, 10000.0) == 2000.0

    def test_loss(self):
        assert calculate_total_pnl(8000.0, 10000.0) == -2000.0

    def test_breakeven(self):
        assert calculate_total_pnl(10000.0, 10000.0) == 0.0


class TestReturnPct:
    def test_positive(self):
        assert calculate_return_pct(2000.0, 10000.0) == 20.0

    def test_negative(self):
        assert calculate_return_pct(-1000.0, 10000.0) == -10.0

    def test_zero_cost(self):
        assert calculate_return_pct(100.0, 0.0) == 0.0


# ── Allocation Tests ────────────────────────────────────────────────


class TestAllocation:
    def test_correct_weights(self):
        positions = [
            PortfolioPosition("BTC", "crypto", 1.0, 50000.0),
            PortfolioPosition("ETH", "crypto", 10.0, 3000.0),
        ]
        prices = {"BTC": 60000.0, "ETH": 4000.0}
        alloc = calculate_allocation(positions, prices)

        assert len(alloc) == 2
        weights = {a["symbol"]: a["weight"] for a in alloc}
        assert abs(weights["BTC"] - 0.6) < 0.01
        assert abs(weights["ETH"] - 0.4) < 0.01
        assert abs(sum(a["weight"] for a in alloc) - 1.0) < 0.001

    def test_single_asset(self):
        positions = [PortfolioPosition("BTC", "crypto", 1.0, 50000.0)]
        prices = {"BTC": 60000.0}
        alloc = calculate_allocation(positions, prices)

        assert len(alloc) == 1
        assert alloc[0]["symbol"] == "BTC"
        assert alloc[0]["weight"] == 1.0

    def test_empty_portfolio(self):
        assert calculate_allocation([], {}) == []

    def test_missing_price_excluded(self):
        positions = [
            PortfolioPosition("BTC", "crypto", 1.0, 50000.0),
            PortfolioPosition("AAPL", "equity", 10, 150.0),
        ]
        prices = {"BTC": 60000.0}
        alloc = calculate_allocation(positions, prices)
        assert len(alloc) == 1
        assert alloc[0]["weight"] == 1.0

    def test_sorted_descending(self):
        positions = [
            PortfolioPosition("ETH", "crypto", 1.0, 3000.0),
            PortfolioPosition("BTC", "crypto", 1.0, 50000.0),
        ]
        prices = {"ETH": 4000.0, "BTC": 60000.0}
        alloc = calculate_allocation(positions, prices)
        assert alloc[0]["symbol"] == "BTC"


class TestLargestPositionWeight:
    def test_returns_largest(self):
        alloc = [
            {"symbol": "BTC", "weight": 0.6},
            {"symbol": "ETH", "weight": 0.4},
        ]
        assert largest_position_weight(alloc) == 0.6

    def test_empty(self):
        assert largest_position_weight([]) == 0.0


class TestAssetCount:
    def test_count(self):
        positions = [
            PortfolioPosition("BTC", "crypto", 1.0, 50000.0),
            PortfolioPosition("AAPL", "equity", 10, 150.0),
        ]
        assert asset_count(positions) == 2

    def test_empty(self):
        assert asset_count([]) == 0


# ── Position Normalization Tests ────────────────────────────────────


class TestNormalizePositions:
    def _make_txn(self, symbol, asset_type, txn_type, quantity, price):
        txn = MagicMock()
        txn.symbol = symbol
        txn.asset_type = asset_type
        txn.transaction_type = txn_type
        txn.quantity = quantity
        txn.price = price
        return txn

    def test_basic_buy(self):
        txns = [self._make_txn("BTC", "crypto", "buy", 1.0, 50000.0)]
        positions = _normalize_positions(txns)
        assert len(positions) == 1
        assert positions[0].symbol == "BTC"
        assert positions[0].asset_type == "crypto"
        assert positions[0].quantity == 1.0
        assert positions[0].avg_cost == 50000.0

    def test_buy_and_partial_sell(self):
        txns = [
            self._make_txn("BTC", "crypto", "buy", 2.0, 50000.0),
            self._make_txn("BTC", "crypto", "sell", 0.5, 55000.0),
        ]
        positions = _normalize_positions(txns)
        assert len(positions) == 1
        assert positions[0].quantity == 1.5

    def test_fully_sold_excluded(self):
        txns = [
            self._make_txn("BTC", "crypto", "buy", 1.0, 50000.0),
            self._make_txn("BTC", "crypto", "sell", 1.0, 55000.0),
        ]
        positions = _normalize_positions(txns)
        assert len(positions) == 0

    def test_stock_mapped_to_equity(self):
        txns = [self._make_txn("AAPL", "stock", "buy", 10, 150.0)]
        positions = _normalize_positions(txns)
        assert positions[0].asset_type == "equity"

    def test_mixed_assets(self):
        txns = [
            self._make_txn("BTC", "crypto", "buy", 0.5, 60000.0),
            self._make_txn("AAPL", "stock", "buy", 10, 150.0),
        ]
        positions = _normalize_positions(txns)
        symbols = {p.symbol for p in positions}
        assert symbols == {"BTC", "AAPL"}


# ── Orchestrator Tests ──────────────────────────────────────────────


class TestGetPortfolioAnalytics:
    def _make_txn(self, symbol, asset_type, txn_type, quantity, price):
        txn = MagicMock()
        txn.symbol = symbol
        txn.asset_type = asset_type
        txn.transaction_type = txn_type
        txn.quantity = quantity
        txn.price = price
        return txn

    @patch(
        "app.services.analytics.portfolio_analytics.get_current_prices_map"
    )
    def test_correct_total_value(self, mock_prices):
        mock_prices.return_value = {"BTC": 60000.0, "AAPL": 170.0}
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            self._make_txn("BTC", "crypto", "buy", 0.5, 50000.0),
            self._make_txn("AAPL", "stock", "buy", 10, 150.0),
        ]
        result = get_portfolio_analytics(db, user_id=1)

        assert result["total_value"] == 31700.0

    @patch(
        "app.services.analytics.portfolio_analytics.get_current_prices_map"
    )
    def test_correct_pnl(self, mock_prices):
        mock_prices.return_value = {"BTC": 60000.0}
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            self._make_txn("BTC", "crypto", "buy", 1.0, 50000.0),
        ]
        result = get_portfolio_analytics(db, user_id=1)

        assert result["total_value"] == 60000.0
        assert result["total_cost"] == 50000.0
        assert result["total_pnl"] == 10000.0
        assert result["return_pct"] == 20.0

    @patch(
        "app.services.analytics.portfolio_analytics.get_current_prices_map"
    )
    def test_correct_return_pct(self, mock_prices):
        mock_prices.return_value = {"AAPL": 200.0}
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            self._make_txn("AAPL", "stock", "buy", 10, 100.0),
        ]
        result = get_portfolio_analytics(db, user_id=1)

        assert result["return_pct"] == 100.0

    @patch(
        "app.services.analytics.portfolio_analytics.get_current_prices_map"
    )
    def test_allocation_correctness(self, mock_prices):
        mock_prices.return_value = {"BTC": 60000.0, "ETH": 4000.0}
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            self._make_txn("BTC", "crypto", "buy", 1.0, 50000.0),
            self._make_txn("ETH", "crypto", "buy", 10.0, 3000.0),
        ]
        result = get_portfolio_analytics(db, user_id=1)

        weights = {a["symbol"]: a["weight"] for a in result["allocation"]}
        assert abs(weights["BTC"] - 0.6) < 0.01
        assert abs(weights["ETH"] - 0.4) < 0.01
        assert abs(sum(a["weight"] for a in result["allocation"]) - 1.0) < 0.001

    @patch(
        "app.services.analytics.portfolio_analytics.get_current_prices_map"
    )
    def test_single_asset(self, mock_prices):
        mock_prices.return_value = {"BTC": 60000.0}
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            self._make_txn("BTC", "crypto", "buy", 1.0, 50000.0),
        ]
        result = get_portfolio_analytics(db, user_id=1)

        assert result["diversification"]["asset_count"] == 1
        assert result["diversification"]["largest_position_pct"] == 1.0
        assert len(result["allocation"]) == 1

    def test_empty_portfolio(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = get_portfolio_analytics(db, user_id=1)

        assert result["total_value"] == 0.0
        assert result["total_cost"] == 0.0
        assert result["total_pnl"] == 0.0
        assert result["return_pct"] == 0.0
        assert result["allocation"] == []
        assert result["diversification"]["asset_count"] == 0
        assert result["diversification"]["largest_position_pct"] == 0.0

    @patch(
        "app.services.analytics.portfolio_analytics.get_current_prices_map"
    )
    def test_missing_market_price(self, mock_prices):
        mock_prices.return_value = {"BTC": 60000.0}
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            self._make_txn("BTC", "crypto", "buy", 1.0, 50000.0),
            self._make_txn("AAPL", "stock", "buy", 10, 150.0),
        ]
        result = get_portfolio_analytics(db, user_id=1)

        # AAPL price missing — only BTC counted in total_value
        assert result["total_value"] == 60000.0
        # cost includes all positions
        assert result["total_cost"] == 51500.0
        assert len(result["allocation"]) == 1
        assert result["allocation"][0]["symbol"] == "BTC"
        # diversification counts all positions regardless of price availability
        assert result["diversification"]["asset_count"] == 2

    @patch(
        "app.services.analytics.portfolio_analytics.get_current_prices_map"
    )
    def test_mixed_asset_types(self, mock_prices):
        mock_prices.return_value = {"BTC": 60000.0, "AAPL": 200.0}
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            self._make_txn("BTC", "crypto", "buy", 0.5, 50000.0),
            self._make_txn("AAPL", "stock", "buy", 10, 150.0),
        ]
        result = get_portfolio_analytics(db, user_id=1)

        assert result["total_value"] == 32000.0
        assert result["total_cost"] == 26500.0
        assert result["total_pnl"] == 5500.0
        assert result["diversification"]["asset_count"] == 2

    @patch(
        "app.services.analytics.portfolio_analytics.get_current_prices_map"
    )
    def test_market_data_service_failure(self, mock_prices):
        mock_prices.side_effect = Exception("service unavailable")
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            self._make_txn("BTC", "crypto", "buy", 1.0, 50000.0),
        ]
        result = get_portfolio_analytics(db, user_id=1)

        # Graceful degradation: value is 0 since no prices available
        assert result["total_value"] == 0.0
        assert result["total_cost"] == 50000.0
        assert result["total_pnl"] == -50000.0
        assert result["allocation"] == []

    @patch(
        "app.services.analytics.portfolio_analytics.get_current_prices_map"
    )
    def test_single_market_data_call(self, mock_prices):
        mock_prices.return_value = {"BTC": 60000.0, "AAPL": 170.0}
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            self._make_txn("BTC", "crypto", "buy", 1.0, 50000.0),
            self._make_txn("AAPL", "stock", "buy", 10, 150.0),
        ]
        get_portfolio_analytics(db, user_id=1)

        mock_prices.assert_called_once()
