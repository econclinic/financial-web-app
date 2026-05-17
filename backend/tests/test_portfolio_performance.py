"""Tests for Phase F — Portfolio Performance API.

Covers:
- Performance service: return computation, closest-snapshot logic, null windows,
  empty/single snapshot edge cases
- Repository: get_latest_snapshot, get_closest_snapshot_at_or_before
- API: GET /portfolio/performance, GET /portfolio/performance/history
  (structure, range filtering, user isolation, ordering, invalid range, auth)
"""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.repositories.portfolio_snapshot_repository import (
    get_closest_snapshot_at_or_before,
    get_latest_snapshot,
    save_snapshot,
)
from app.services import portfolio_analytics
from app.services.performance.portfolio_performance_service import (
    get_performance_summary,
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
    db,
    user_id: int,
    ts: datetime,
    total_value: float,
    total_cost: float = 8000.0,
    total_pnl: float | None = None,
    asset_count: int = 3,
) -> PortfolioSnapshot:
    if total_pnl is None:
        total_pnl = total_value - total_cost
    snap = PortfolioSnapshot(
        user_id=user_id,
        timestamp=ts,
        total_value=total_value,
        total_cost=total_cost,
        total_pnl=total_pnl,
        asset_count=asset_count,
    )
    return save_snapshot(db, snap)


# ── Repository helper tests ────────────────────────────────────────


class TestRepositoryHelpers:
    def test_get_latest_snapshot(self):
        _reset_db()
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now - timedelta(days=2), 10000.0)
            _insert_snapshot(db, 1, now - timedelta(days=1), 10500.0)
            _insert_snapshot(db, 1, now, 11000.0)

            latest = get_latest_snapshot(db, 1)
            assert latest is not None
            assert latest.total_value == 11000.0
        finally:
            db.close()

    def test_get_latest_snapshot_none(self):
        _reset_db()
        db = SessionLocal()
        try:
            assert get_latest_snapshot(db, 999) is None
        finally:
            db.close()

    def test_closest_snapshot_exact_match(self):
        _reset_db()
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            target = now - timedelta(days=7)
            _insert_snapshot(db, 1, target, 9500.0)
            _insert_snapshot(db, 1, now, 10000.0)

            snap = get_closest_snapshot_at_or_before(db, 1, target)
            assert snap is not None
            assert snap.total_value == 9500.0
        finally:
            db.close()

    def test_closest_snapshot_uses_prior(self):
        _reset_db()
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now - timedelta(days=8), 9200.0)
            _insert_snapshot(db, 1, now - timedelta(days=6), 9800.0)
            _insert_snapshot(db, 1, now, 10000.0)

            target = now - timedelta(days=7)
            snap = get_closest_snapshot_at_or_before(db, 1, target)
            assert snap is not None
            assert snap.total_value == 9200.0
        finally:
            db.close()

    def test_closest_snapshot_none_when_no_prior(self):
        _reset_db()
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now - timedelta(days=3), 10000.0)

            target = now - timedelta(days=7)
            snap = get_closest_snapshot_at_or_before(db, 1, target)
            assert snap is None
        finally:
            db.close()


# ── Performance service tests ───────────────────────────────────────


class TestPerformanceService:
    def test_returns_all_windows(self):
        _reset_db()
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now - timedelta(days=400), 8000.0)
            _insert_snapshot(db, 1, now - timedelta(days=100), 9000.0)
            _insert_snapshot(db, 1, now - timedelta(days=31), 9500.0)
            _insert_snapshot(db, 1, now - timedelta(days=8), 9800.0)
            _insert_snapshot(db, 1, now, 10000.0)

            result = get_performance_summary(db, 1)
            assert result is not None
            assert result["current_value"] == 10000.0

            r = result["returns"]
            assert r["7d"] is not None
            assert r["7d"]["absolute"] == 200.0
            assert r["30d"] is not None
            assert r["30d"]["absolute"] == 500.0
            assert r["90d"] is not None
            assert r["90d"]["absolute"] == 1000.0
            assert r["1y"] is not None
            assert r["1y"]["absolute"] == 2000.0
        finally:
            db.close()

    def test_uses_closest_prior_snapshot(self):
        _reset_db()
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now - timedelta(days=10), 9500.0)
            _insert_snapshot(db, 1, now, 10000.0)

            result = get_performance_summary(db, 1)
            assert result is not None
            assert result["returns"]["7d"] is not None
            assert result["returns"]["7d"]["absolute"] == 500.0
        finally:
            db.close()

    def test_null_when_no_prior_snapshot(self):
        _reset_db()
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            # Only snapshots within the last 3 days — no snapshot at or before 7d cutoff
            _insert_snapshot(db, 1, now - timedelta(days=3), 9800.0)
            _insert_snapshot(db, 1, now, 10000.0)

            result = get_performance_summary(db, 1)
            assert result is not None
            # 7d target = now - 7d; closest prior is now - 3d which is AFTER the target
            assert result["returns"]["7d"] is None
            assert result["returns"]["30d"] is None
            assert result["returns"]["90d"] is None
            assert result["returns"]["1y"] is None
        finally:
            db.close()

    def test_empty_snapshot_history(self):
        _reset_db()
        db = SessionLocal()
        try:
            result = get_performance_summary(db, 1)
            assert result is None
        finally:
            db.close()

    def test_single_snapshot(self):
        _reset_db()
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now, 10000.0)

            result = get_performance_summary(db, 1)
            assert result is not None
            assert result["current_value"] == 10000.0
            for key in ("7d", "30d", "90d", "1y"):
                assert result["returns"][key] is None
        finally:
            db.close()

    def test_percent_return_calculation(self):
        _reset_db()
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            _insert_snapshot(db, 1, now - timedelta(days=10), 10000.0)
            _insert_snapshot(db, 1, now, 10500.0)

            result = get_performance_summary(db, 1)
            assert result is not None
            ret = result["returns"]["7d"]
            assert ret is not None
            assert ret["absolute"] == 500.0
            assert ret["percent"] == 0.05
        finally:
            db.close()


# ── API endpoint tests ──────────────────────────────────────────────


def test_performance_endpoint_structure():
    _reset_db()
    token = _register("perf1@test.com")
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        _insert_snapshot(db, 1, now - timedelta(days=10), 9500.0)
        _insert_snapshot(db, 1, now, 10000.0)
    finally:
        db.close()

    resp = client.get("/api/portfolio/performance", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "current_value" in data
    assert "as_of" in data
    assert "returns" in data
    returns = data["returns"]
    assert "seven_d" in returns
    assert "thirty_d" in returns
    assert "ninety_d" in returns
    assert "one_y" in returns


def test_performance_endpoint_empty():
    _reset_db()
    token = _register("perf2@test.com")

    resp = client.get("/api/portfolio/performance", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_value"] == 0.0


def test_performance_endpoint_unauthenticated():
    resp = client.get("/api/portfolio/performance")
    assert resp.status_code in (401, 403)


def test_performance_history_endpoint():
    _reset_db()
    token = _register("perf3@test.com")
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        for i in range(5):
            _insert_snapshot(db, 1, now - timedelta(days=4 - i), 10000.0 + i * 100)
    finally:
        db.close()

    resp = client.get("/api/portfolio/performance/history?range=7d", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["range"] == "7d"
    assert len(data["points"]) == 5
    for pt in data["points"]:
        assert "timestamp" in pt
        assert "total_value" in pt
        assert "total_cost" in pt
        assert "total_pnl" in pt


def test_performance_history_ordered():
    _reset_db()
    token = _register("perf4@test.com")
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        for i in range(3):
            _insert_snapshot(db, 1, now - timedelta(days=2 - i), 10000.0 + i * 100)
    finally:
        db.close()

    resp = client.get("/api/portfolio/performance/history?range=30d", headers=_auth(token))
    data = resp.json()
    timestamps = [p["timestamp"] for p in data["points"]]
    assert timestamps == sorted(timestamps)


def test_performance_history_range_filtering():
    _reset_db()
    token = _register("perf5@test.com")
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        _insert_snapshot(db, 1, now - timedelta(days=20), 9000.0)
        _insert_snapshot(db, 1, now - timedelta(days=3), 9800.0)
        _insert_snapshot(db, 1, now, 10000.0)
    finally:
        db.close()

    resp7 = client.get("/api/portfolio/performance/history?range=7d", headers=_auth(token))
    resp30 = client.get("/api/portfolio/performance/history?range=30d", headers=_auth(token))
    assert len(resp7.json()["points"]) == 2
    assert len(resp30.json()["points"]) == 3


def test_performance_history_invalid_range():
    _reset_db()
    token = _register("perf6@test.com")

    resp = client.get("/api/portfolio/performance/history?range=2w", headers=_auth(token))
    assert resp.status_code == 422


def test_performance_history_user_isolation():
    _reset_db()
    token1 = _register("perfiso1@test.com")
    token2 = _register("perfiso2@test.com")
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        _insert_snapshot(db, 1, now, 10000.0)
        _insert_snapshot(db, 2, now, 20000.0)
    finally:
        db.close()

    resp1 = client.get("/api/portfolio/performance/history?range=30d", headers=_auth(token1))
    resp2 = client.get("/api/portfolio/performance/history?range=30d", headers=_auth(token2))

    assert len(resp1.json()["points"]) == 1
    assert resp1.json()["points"][0]["total_value"] == 10000.0

    assert len(resp2.json()["points"]) == 1
    assert resp2.json()["points"][0]["total_value"] == 20000.0


def test_performance_history_unauthenticated():
    resp = client.get("/api/portfolio/performance/history")
    assert resp.status_code in (401, 403)
