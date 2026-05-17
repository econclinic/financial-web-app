"""Tests for the Phase E Portfolio Snapshot & History API.

Covers:
- Snapshot creation via service layer
- Snapshot persistence and retrieval via repository
- POST /portfolio/snapshot endpoint
- GET /portfolio/history endpoint with range filtering
- Snapshot values match analytics output
- History returns correctly ordered timestamps
- Edge cases: empty portfolio, no snapshots
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.repositories.portfolio_snapshot_repository import (
    get_recent_snapshots,
    get_snapshots,
    save_snapshot,
)
from app.services import portfolio_analytics
from app.services.portfolio_snapshot_service import create_snapshot

client = TestClient(app)

MOCK_PRICES = {"BTC": 65000.0, "ETH": 3200.0, "AAPL": 190.0}


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


def _add_txn(token: str, symbol: str, asset_type: str, txn_type: str, qty: float, price: float):
    client.post(
        "/api/portfolio/transactions",
        json={
            "symbol": symbol,
            "asset_type": asset_type,
            "transaction_type": txn_type,
            "quantity": qty,
            "price": price,
        },
        headers=_auth(token),
    )


def _mock_prices_map(symbols=None):
    if symbols is None:
        return MOCK_PRICES
    return {s: MOCK_PRICES[s] for s in symbols if s in MOCK_PRICES}


# ── Repository Tests ────────────────────────────────────────────────


class TestSnapshotRepository:
    def test_save_and_retrieve(self):
        _reset_db()
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            snap = PortfolioSnapshot(
                user_id=999,
                total_value=10000.0,
                total_cost=8000.0,
                total_pnl=2000.0,
                asset_count=3,
            )
            saved = save_snapshot(db, snap)
            assert saved.id is not None
            assert saved.total_value == 10000.0

            now = datetime.now(timezone.utc)
            results = get_snapshots(db, 999, now - timedelta(hours=1), now + timedelta(hours=1))
            assert len(results) == 1
            assert results[0].total_value == 10000.0
        finally:
            db.close()

    def test_snapshots_ordered_by_timestamp(self):
        _reset_db()
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            for i in range(3):
                snap = PortfolioSnapshot(
                    user_id=999,
                    timestamp=now - timedelta(days=2 - i),
                    total_value=10000.0 + i * 100,
                    total_cost=8000.0,
                    total_pnl=2000.0 + i * 100,
                    asset_count=3,
                )
                save_snapshot(db, snap)

            results = get_snapshots(db, 999, now - timedelta(days=5), now + timedelta(days=1))
            assert len(results) == 3
            assert results[0].total_value == 10000.0
            assert results[1].total_value == 10100.0
            assert results[2].total_value == 10200.0
        finally:
            db.close()

    def test_range_filtering(self):
        _reset_db()
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            for i in range(5):
                snap = PortfolioSnapshot(
                    user_id=999,
                    timestamp=now - timedelta(days=4 - i),
                    total_value=10000.0 + i * 100,
                    total_cost=8000.0,
                    total_pnl=2000.0 + i * 100,
                    asset_count=3,
                )
                save_snapshot(db, snap)

            # Only last 2 days
            results = get_snapshots(
                db, 999, now - timedelta(days=1, hours=12), now + timedelta(hours=1)
            )
            assert len(results) == 2
        finally:
            db.close()

    def test_user_isolation(self):
        _reset_db()
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            for uid in (100, 200):
                snap = PortfolioSnapshot(
                    user_id=uid,
                    total_value=10000.0,
                    total_cost=8000.0,
                    total_pnl=2000.0,
                    asset_count=3,
                )
                save_snapshot(db, snap)

            now = datetime.now(timezone.utc)
            results = get_snapshots(db, 100, now - timedelta(hours=1), now + timedelta(hours=1))
            assert len(results) == 1
        finally:
            db.close()

    def test_get_recent_snapshots(self):
        _reset_db()
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            for i in range(5):
                snap = PortfolioSnapshot(
                    user_id=999,
                    timestamp=now - timedelta(days=4 - i),
                    total_value=10000.0 + i * 100,
                    total_cost=8000.0,
                    total_pnl=2000.0 + i * 100,
                    asset_count=3,
                )
                save_snapshot(db, snap)

            results = get_recent_snapshots(db, 999, limit=3)
            assert len(results) == 3
            # Should be ascending order (oldest first among the 3 most recent)
            assert results[0].total_value == 10200.0
            assert results[2].total_value == 10400.0
        finally:
            db.close()


# ── Snapshot Service Tests ──────────────────────────────────────────


class TestSnapshotService:
    @patch(
        "app.services.analytics.portfolio_analytics.get_current_prices_map"
    )
    def test_snapshot_values_match_analytics(self, mock_prices):
        mock_prices.return_value = {"BTC": 65000.0}
        _reset_db()
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            # Insert a transaction directly
            from app.models.portfolio import PortfolioTransaction

            txn = PortfolioTransaction(
                user_id=1,
                symbol="BTC",
                asset_type="crypto",
                transaction_type="buy",
                quantity=0.5,
                price=50000.0,
            )
            db.add(txn)
            db.commit()

            snap = create_snapshot(db, user_id=1)
            assert snap.total_value == 32500.0  # 0.5 * 65000
            assert snap.total_cost == 25000.0  # 0.5 * 50000
            assert snap.total_pnl == 7500.0
            assert snap.asset_count == 1
            assert snap.id is not None
        finally:
            db.close()

    def test_empty_portfolio_snapshot(self):
        _reset_db()
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            snap = create_snapshot(db, user_id=1)
            assert snap.total_value == 0.0
            assert snap.total_cost == 0.0
            assert snap.total_pnl == 0.0
            assert snap.asset_count == 0
        finally:
            db.close()


# ── API Endpoint Tests ──────────────────────────────────────────────


@patch(
    "app.services.analytics.portfolio_analytics.get_current_prices_map",
    side_effect=_mock_prices_map,
)
def test_snapshot_endpoint_creates_snapshot(mock_prices):
    _reset_db()
    token = _register("snap1@test.com")
    _add_txn(token, "BTC", "crypto", "buy", 1.0, 50000.0)

    resp = client.post("/api/portfolio/snapshot", headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_value"] == 65000.0
    assert data["total_cost"] == 50000.0
    assert data["total_pnl"] == 15000.0
    assert data["asset_count"] == 1
    assert "timestamp" in data


@patch(
    "app.services.analytics.portfolio_analytics.get_current_prices_map",
    side_effect=_mock_prices_map,
)
def test_snapshot_endpoint_empty_portfolio(mock_prices):
    _reset_db()
    token = _register("snap2@test.com")

    resp = client.post("/api/portfolio/snapshot", headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_value"] == 0.0
    assert data["total_cost"] == 0.0
    assert data["total_pnl"] == 0.0
    assert data["asset_count"] == 0


@patch(
    "app.services.analytics.portfolio_analytics.get_current_prices_map",
    side_effect=_mock_prices_map,
)
def test_history_endpoint_returns_snapshots(mock_prices):
    _reset_db()
    token = _register("hist1@test.com")
    _add_txn(token, "BTC", "crypto", "buy", 1.0, 50000.0)

    # Create a few snapshots
    client.post("/api/portfolio/snapshot", headers=_auth(token))
    client.post("/api/portfolio/snapshot", headers=_auth(token))

    resp = client.get("/api/portfolio/history?range=30d", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["range"] == "30d"
    assert len(data["points"]) == 2
    for point in data["points"]:
        assert "timestamp" in point
        assert "value" in point
        assert point["value"] == 65000.0


@patch(
    "app.services.analytics.portfolio_analytics.get_current_prices_map",
    side_effect=_mock_prices_map,
)
def test_history_endpoint_empty(mock_prices):
    _reset_db()
    token = _register("hist2@test.com")

    resp = client.get("/api/portfolio/history?range=7d", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["range"] == "7d"
    assert data["points"] == []


def test_history_endpoint_invalid_range():
    _reset_db()
    token = _register("hist3@test.com")

    resp = client.get("/api/portfolio/history?range=2w", headers=_auth(token))
    assert resp.status_code == 422


def test_snapshot_endpoint_unauthenticated():
    resp = client.post("/api/portfolio/snapshot")
    assert resp.status_code in (401, 403)


def test_history_endpoint_unauthenticated():
    resp = client.get("/api/portfolio/history")
    assert resp.status_code in (401, 403)


@patch(
    "app.services.analytics.portfolio_analytics.get_current_prices_map",
    side_effect=_mock_prices_map,
)
def test_history_timestamps_ordered(mock_prices):
    _reset_db()
    token = _register("hist4@test.com")
    _add_txn(token, "AAPL", "stock", "buy", 10, 150.0)

    # Create snapshots
    for _ in range(3):
        client.post("/api/portfolio/snapshot", headers=_auth(token))

    resp = client.get("/api/portfolio/history?range=30d", headers=_auth(token))
    data = resp.json()
    timestamps = [p["timestamp"] for p in data["points"]]
    assert timestamps == sorted(timestamps)


@patch(
    "app.services.analytics.portfolio_analytics.get_current_prices_map",
    side_effect=_mock_prices_map,
)
def test_snapshot_user_isolation(mock_prices):
    _reset_db()
    token1 = _register("iso1@test.com")
    token2 = _register("iso2@test.com")

    _add_txn(token1, "BTC", "crypto", "buy", 1.0, 50000.0)
    client.post("/api/portfolio/snapshot", headers=_auth(token1))

    _add_txn(token2, "AAPL", "stock", "buy", 10, 150.0)
    client.post("/api/portfolio/snapshot", headers=_auth(token2))

    resp1 = client.get("/api/portfolio/history?range=30d", headers=_auth(token1))
    resp2 = client.get("/api/portfolio/history?range=30d", headers=_auth(token2))

    assert len(resp1.json()["points"]) == 1
    assert resp1.json()["points"][0]["value"] == 65000.0

    assert len(resp2.json()["points"]) == 1
    assert resp2.json()["points"][0]["value"] == 1900.0
