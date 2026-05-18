"""Tests for Phase H — Portfolio Performance Engine.

Covers:
- Performance summary: range returns, max drawdown, snapshot-based
- Contribution: per-asset PnL contribution, weights
- Performers: best/worst by return, limit, sorting
- Edge cases: empty portfolios, zero values, missing prices, single snapshot
- API endpoints: structure, auth, user isolation
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.services import portfolio_analytics
from app.services.analytics.portfolio_performance_engine import (
    _compute_max_drawdown,
    get_contribution,
    get_performers,
    get_range_performance,
)

client = TestClient(app)


def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    portfolio_analytics._overview_cache.clear()


def _register(email: str, password: str = "Test1234!") -> str:
    client.post("/api/auth/register", json={"email": email, "password": password})
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _insert_snapshot(
    db, user_id: int, ts: datetime, total_value: float,
    total_cost: float = 0.0, total_pnl: float = 0.0, asset_count: int = 0,
):
    snap = PortfolioSnapshot(
        user_id=user_id,
        timestamp=ts,
        total_value=total_value,
        total_cost=total_cost,
        total_pnl=total_pnl,
        asset_count=asset_count,
    )
    db.add(snap)
    db.commit()


def _add_transaction(
    token: str,
    symbol: str,
    asset_type: str,
    quantity: float,
    price: float,
    txn_type: str = "buy",
):
    client.post(
        "/api/portfolio/transactions",
        json={
            "symbol": symbol,
            "asset_type": asset_type,
            "transaction_type": txn_type,
            "quantity": quantity,
            "price": price,
        },
        headers=_auth(token),
    )


def _mock_prices(prices: dict[str, float]):
    return patch(
        "app.services.analytics.portfolio_performance_engine.get_current_prices_map",
        return_value=prices,
    )


# ── Max drawdown helper tests ──────────────────────────────────────


class TestMaxDrawdown:
    def test_drawdown_basic(self):
        values = [100.0, 110.0, 90.0, 105.0, 95.0]
        dd = _compute_max_drawdown(values)
        # Peak 110, trough 90 → dd = (90-110)/110 = -0.1818...
        assert round(dd, 4) == -0.1818

    def test_drawdown_monotonic_up(self):
        values = [100.0, 110.0, 120.0, 130.0]
        assert _compute_max_drawdown(values) == 0.0

    def test_drawdown_single_value(self):
        assert _compute_max_drawdown([100.0]) == 0.0

    def test_drawdown_empty(self):
        assert _compute_max_drawdown([]) == 0.0

    def test_drawdown_all_same(self):
        assert _compute_max_drawdown([100.0, 100.0, 100.0]) == 0.0


# ── Performance summary service tests ──────────────────────────────


class TestRangePerformance:
    def test_performance_multiple_snapshots(self):
        _reset_db()
        _register("rp1@test.com")
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now - timedelta(days=20), 10000.0)
            _insert_snapshot(db, 1, now - timedelta(days=10), 11000.0)
            _insert_snapshot(db, 1, now - timedelta(days=5), 10500.0)
            _insert_snapshot(db, 1, now, 11500.0)

            result = get_range_performance(db, 1, "30d")
            assert result["starting_value"] == 10000.0
            assert result["ending_value"] == 11500.0
            assert result["absolute_return"] == 1500.0
            assert abs(result["total_return"] - 0.15) < 0.001
            assert result["snapshot_count"] == 4
        finally:
            db.close()

    def test_performance_empty_range(self):
        _reset_db()
        _register("rp2@test.com")
        db = SessionLocal()
        try:
            result = get_range_performance(db, 1, "7d")
            assert result["starting_value"] == 0.0
            assert result["ending_value"] == 0.0
            assert result["snapshot_count"] == 0
            assert result["start_timestamp"] is None
        finally:
            db.close()

    def test_performance_single_snapshot(self):
        _reset_db()
        _register("rp3@test.com")
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now, 10000.0)

            result = get_range_performance(db, 1, "30d")
            assert result["starting_value"] == 10000.0
            assert result["ending_value"] == 10000.0
            assert result["absolute_return"] == 0.0
            assert result["max_drawdown"] == 0.0
            assert result["snapshot_count"] == 1
        finally:
            db.close()

    def test_performance_zero_starting_value(self):
        _reset_db()
        _register("rp4@test.com")
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now - timedelta(days=5), 0.0)
            _insert_snapshot(db, 1, now, 5000.0)

            result = get_range_performance(db, 1, "7d")
            assert result["total_return"] == 0.0
            assert result["absolute_return"] == 5000.0
        finally:
            db.close()

    def test_performance_with_drawdown(self):
        _reset_db()
        _register("rp5@test.com")
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now - timedelta(days=20), 10000.0)
            _insert_snapshot(db, 1, now - timedelta(days=15), 12000.0)
            _insert_snapshot(db, 1, now - timedelta(days=10), 9000.0)
            _insert_snapshot(db, 1, now, 11000.0)

            result = get_range_performance(db, 1, "30d")
            # Peak 12000, trough 9000 → dd = (9000-12000)/12000 = -0.25
            assert result["max_drawdown"] == -0.25
            assert result["max_drawdown_pct"] == -25.0
        finally:
            db.close()

    def test_performance_all_range(self):
        _reset_db()
        _register("rp6@test.com")
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now - timedelta(days=400), 8000.0)
            _insert_snapshot(db, 1, now, 12000.0)

            result = get_range_performance(db, 1, "all")
            assert result["range"] == "all"
            assert result["snapshot_count"] == 2
            assert result["starting_value"] == 8000.0
            assert result["ending_value"] == 12000.0
        finally:
            db.close()

    def test_performance_user_isolation(self):
        _reset_db()
        _register("rp7a@test.com")
        _register("rp7b@test.com")
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now - timedelta(days=5), 10000.0)
            _insert_snapshot(db, 1, now, 12000.0)
            _insert_snapshot(db, 2, now - timedelta(days=5), 5000.0)
            _insert_snapshot(db, 2, now, 4000.0)

            r1 = get_range_performance(db, 1, "7d")
            r2 = get_range_performance(db, 2, "7d")
            assert r1["absolute_return"] == 2000.0
            assert r2["absolute_return"] == -1000.0
        finally:
            db.close()


# ── Contribution service tests ─────────────────────────────────────


class TestContribution:
    def test_contribution_basic(self):
        _reset_db()
        token = _register("ct1@test.com")
        _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
        _add_transaction(token, "AAPL", "stock", 10.0, 150.0)

        db = SessionLocal()
        try:
            with _mock_prices({"BTC": 35000.0, "AAPL": 180.0}):
                result = get_contribution(db, 1)
            assert result["total_contribution"] != 0
            assert len(result["assets"]) == 2
            # BTC pnl: 35000 - 30000 = 5000
            # AAPL pnl: (10*180) - (10*150) = 300
            btc = next(a for a in result["assets"] if a["symbol"] == "BTC")
            assert btc["pnl"] == 5000.0
            assert btc["contribution"] == 5000.0
        finally:
            db.close()

    def test_contribution_weights_sum(self):
        _reset_db()
        token = _register("ct2@test.com")
        _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
        _add_transaction(token, "AAPL", "stock", 10.0, 150.0)

        db = SessionLocal()
        try:
            with _mock_prices({"BTC": 35000.0, "AAPL": 180.0}):
                result = get_contribution(db, 1)
            weights = [a["contribution_weight"] for a in result["assets"]]
            assert abs(sum(weights) - 1.0) < 0.01
        finally:
            db.close()

    def test_contribution_empty_portfolio(self):
        _reset_db()
        _register("ct3@test.com")

        db = SessionLocal()
        try:
            result = get_contribution(db, 1)
            assert result["total_contribution"] == 0.0
            assert result["assets"] == []
        finally:
            db.close()

    def test_contribution_missing_prices(self):
        _reset_db()
        token = _register("ct4@test.com")
        _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)

        db = SessionLocal()
        try:
            with _mock_prices({}):
                result = get_contribution(db, 1)
            # Price defaults to 0, so value=0, pnl = -cost_basis
            assert len(result["assets"]) == 1
            assert result["assets"][0]["value"] == 0.0
        finally:
            db.close()

    def test_contribution_sorting(self):
        _reset_db()
        token = _register("ct5@test.com")
        _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
        _add_transaction(token, "ETH", "crypto", 10.0, 2000.0)

        db = SessionLocal()
        try:
            with _mock_prices({"BTC": 35000.0, "ETH": 2500.0}):
                result = get_contribution(db, 1)
            contributions = [a["contribution"] for a in result["assets"]]
            assert contributions == sorted(contributions, reverse=True)
        finally:
            db.close()


# ── Performer service tests ────────────────────────────────────────


class TestPerformers:
    def test_performers_basic(self):
        _reset_db()
        token = _register("pf1@test.com")
        _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
        _add_transaction(token, "AAPL", "stock", 10.0, 200.0)

        db = SessionLocal()
        try:
            with _mock_prices({"BTC": 40000.0, "AAPL": 150.0}):
                result = get_performers(db, 1)
            assert len(result["best"]) == 2
            assert len(result["worst"]) == 2
            # BTC: return = 10000/30000 = 0.3333
            # AAPL: return = -500/2000 = -0.25
            assert result["best"][0]["symbol"] == "BTC"
            assert result["worst"][0]["symbol"] == "AAPL"
        finally:
            db.close()

    def test_performers_limit(self):
        _reset_db()
        token = _register("pf2@test.com")
        for i in range(7):
            _add_transaction(token, f"S{i}", "stock", 1.0, 100.0 + i * 10)

        db = SessionLocal()
        try:
            prices = {f"S{i}": 150.0 for i in range(7)}
            with _mock_prices(prices):
                result = get_performers(db, 1, limit=3)
            assert len(result["best"]) == 3
            assert len(result["worst"]) == 3
        finally:
            db.close()

    def test_performers_small_cost_basis(self):
        _reset_db()
        token = _register("pf3@test.com")
        _add_transaction(token, "CHEAP", "stock", 1.0, 0.01)

        db = SessionLocal()
        try:
            with _mock_prices({"CHEAP": 100.0}):
                result = get_performers(db, 1)
            assert len(result["best"]) == 1
            assert result["best"][0]["return"] > 0
        finally:
            db.close()

    def test_performers_empty_portfolio(self):
        _reset_db()
        _register("pf4@test.com")

        db = SessionLocal()
        try:
            result = get_performers(db, 1)
            assert result["best"] == []
            assert result["worst"] == []
        finally:
            db.close()

    def test_performers_deterministic_sorting(self):
        _reset_db()
        token = _register("pf5@test.com")
        _add_transaction(token, "B", "stock", 1.0, 100.0)
        _add_transaction(token, "A", "stock", 1.0, 100.0)

        db = SessionLocal()
        try:
            with _mock_prices({"A": 150.0, "B": 150.0}):
                result = get_performers(db, 1)
            # Equal return → tiebreak by symbol ascending
            assert result["best"][0]["symbol"] == "A"
            assert result["best"][1]["symbol"] == "B"
        finally:
            db.close()


# ── API endpoint tests ──────────────────────────────────────────────


def test_performance_api_structure():
    _reset_db()
    token = _register("api1@test.com")
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        _insert_snapshot(db, 1, now - timedelta(days=10), 10000.0)
        _insert_snapshot(db, 1, now, 11000.0)
    finally:
        db.close()

    resp = client.get("/api/portfolio/performance?range=30d", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["range"] == "30d"
    assert data["starting_value"] == 10000.0
    assert data["ending_value"] == 11000.0
    assert data["absolute_return"] == 1000.0
    assert data["snapshot_count"] == 2
    assert "max_drawdown" in data
    assert "total_return" in data
    assert "total_return_pct" in data


def test_performance_api_invalid_range():
    _reset_db()
    token = _register("api2@test.com")
    resp = client.get("/api/portfolio/performance?range=2w", headers=_auth(token))
    assert resp.status_code == 422


def test_performance_api_all_range():
    _reset_db()
    token = _register("api3@test.com")
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        _insert_snapshot(db, 1, now - timedelta(days=400), 8000.0)
        _insert_snapshot(db, 1, now, 12000.0)
    finally:
        db.close()

    resp = client.get("/api/portfolio/performance?range=all", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["range"] == "all"
    assert resp.json()["snapshot_count"] == 2


def test_performance_api_unauthenticated():
    resp = client.get("/api/portfolio/performance")
    assert resp.status_code in (401, 403)


def test_contribution_api_structure():
    _reset_db()
    token = _register("api4@test.com")
    _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)

    with _mock_prices({"BTC": 35000.0}):
        resp = client.get("/api/portfolio/contribution", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "total_contribution" in data
    assert "assets" in data
    assert len(data["assets"]) == 1
    asset = data["assets"][0]
    assert "symbol" in asset
    assert "asset_type" in asset
    assert "value" in asset
    assert "cost_basis" in asset
    assert "pnl" in asset
    assert "contribution" in asset
    assert "contribution_weight" in asset


def test_contribution_api_unauthenticated():
    resp = client.get("/api/portfolio/contribution")
    assert resp.status_code in (401, 403)


def test_performers_api_structure():
    _reset_db()
    token = _register("api5@test.com")
    _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
    _add_transaction(token, "AAPL", "stock", 10.0, 200.0)

    with _mock_prices({"BTC": 40000.0, "AAPL": 150.0}):
        resp = client.get("/api/portfolio/performers", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "best" in data
    assert "worst" in data
    best = data["best"][0]
    assert "symbol" in best
    assert "return" in best
    assert "return_pct" in best
    assert "pnl" in best


def test_performers_api_with_limit():
    _reset_db()
    token = _register("api6@test.com")
    for i in range(7):
        _add_transaction(token, f"S{i}", "stock", 1.0, 100.0 + i * 10)

    prices = {f"S{i}": 150.0 for i in range(7)}
    with _mock_prices(prices):
        resp = client.get("/api/portfolio/performers?limit=3", headers=_auth(token))
    assert resp.status_code == 200
    assert len(resp.json()["best"]) == 3
    assert len(resp.json()["worst"]) == 3


def test_performers_api_unauthenticated():
    resp = client.get("/api/portfolio/performers")
    assert resp.status_code in (401, 403)
