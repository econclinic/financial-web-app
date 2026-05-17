"""Tests for Phase G — Portfolio Allocation & Exposure API.

Covers:
- Allocation service: per-asset weights, total value, sorting
- Exposure service: asset class aggregation
- Top positions: ranking and limit
- Edge cases: empty portfolio, zero total value, single asset
- API endpoints: structure, auth, user isolation
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.services import portfolio_analytics
from app.services.allocation.portfolio_allocation_service import (
    get_portfolio_allocation,
    get_portfolio_exposure,
    get_top_positions,
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
        "app.services.allocation.portfolio_allocation_service.get_current_prices_map",
        return_value=prices,
    )


# ── Service tests ───────────────────────────────────────────────────


class TestAllocationService:
    def test_allocation_multiple_assets(self):
        _reset_db()
        token = _register("alloc1@test.com")
        _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
        _add_transaction(token, "AAPL", "stock", 10.0, 150.0)
        _add_transaction(token, "ETH", "crypto", 5.0, 2000.0)

        db = SessionLocal()
        try:
            with _mock_prices({"BTC": 40000.0, "AAPL": 180.0, "ETH": 2500.0}):
                result = get_portfolio_allocation(db, 1)

            assert result["total_value"] == 54300.0  # 40000 + 1800 + 12500
            assert len(result["assets"]) == 3
            # Sorted descending by value
            assert result["assets"][0]["symbol"] == "BTC"
            assert result["assets"][1]["symbol"] == "ETH"
            assert result["assets"][2]["symbol"] == "AAPL"
        finally:
            db.close()

    def test_weight_calculation(self):
        _reset_db()
        token = _register("alloc2@test.com")
        _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
        _add_transaction(token, "AAPL", "stock", 10.0, 150.0)

        db = SessionLocal()
        try:
            with _mock_prices({"BTC": 50000.0, "AAPL": 200.0}):
                result = get_portfolio_allocation(db, 1)

            total = result["total_value"]  # 50000 + 2000 = 52000
            assert total == 52000.0
            weights = {a["symbol"]: a["weight"] for a in result["assets"]}
            assert abs(sum(w for w in weights.values() if w is not None) - 1.0) < 0.01
        finally:
            db.close()

    def test_total_portfolio_value(self):
        _reset_db()
        token = _register("alloc3@test.com")
        _add_transaction(token, "BTC", "crypto", 2.0, 30000.0)

        db = SessionLocal()
        try:
            with _mock_prices({"BTC": 35000.0}):
                result = get_portfolio_allocation(db, 1)
            assert result["total_value"] == 70000.0
        finally:
            db.close()

    def test_empty_portfolio(self):
        _reset_db()
        _register("alloc4@test.com")

        db = SessionLocal()
        try:
            result = get_portfolio_allocation(db, 1)
            assert result["total_value"] == 0.0
            assert result["assets"] == []
        finally:
            db.close()

    def test_zero_total_value(self):
        _reset_db()
        token = _register("alloc5@test.com")
        _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)

        db = SessionLocal()
        try:
            with _mock_prices({"BTC": 0.0}):
                result = get_portfolio_allocation(db, 1)
            assert result["total_value"] == 0.0
            assert result["assets"][0]["weight"] is None
        finally:
            db.close()

    def test_sorting_deterministic(self):
        _reset_db()
        token = _register("alloc6@test.com")
        _add_transaction(token, "A", "stock", 1.0, 10.0)
        _add_transaction(token, "B", "stock", 1.0, 20.0)
        _add_transaction(token, "C", "stock", 1.0, 30.0)

        db = SessionLocal()
        try:
            with _mock_prices({"A": 100.0, "B": 200.0, "C": 300.0}):
                result = get_portfolio_allocation(db, 1)
            values = [a["value"] for a in result["assets"]]
            assert values == sorted(values, reverse=True)
        finally:
            db.close()


class TestExposureService:
    def test_exposure_aggregation(self):
        _reset_db()
        token = _register("exp1@test.com")
        _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
        _add_transaction(token, "ETH", "crypto", 5.0, 2000.0)
        _add_transaction(token, "AAPL", "stock", 10.0, 150.0)

        db = SessionLocal()
        try:
            with _mock_prices({"BTC": 40000.0, "ETH": 2500.0, "AAPL": 180.0}):
                result = get_portfolio_exposure(db, 1)

            assert result["total_value"] == 54300.0
            exp_map = {e["asset_class"]: e for e in result["exposures"]}
            assert "crypto" in exp_map
            assert "equity" in exp_map
            assert exp_map["crypto"]["value"] == 52500.0  # 40000 + 12500
            assert exp_map["equity"]["value"] == 1800.0
        finally:
            db.close()

    def test_exposure_empty_portfolio(self):
        _reset_db()
        _register("exp2@test.com")

        db = SessionLocal()
        try:
            result = get_portfolio_exposure(db, 1)
            assert result["total_value"] == 0.0
            assert result["exposures"] == []
        finally:
            db.close()

    def test_exposure_weights_sum_to_one(self):
        _reset_db()
        token = _register("exp3@test.com")
        _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
        _add_transaction(token, "AAPL", "stock", 10.0, 150.0)

        db = SessionLocal()
        try:
            with _mock_prices({"BTC": 40000.0, "AAPL": 180.0}):
                result = get_portfolio_exposure(db, 1)
            weights = [e["weight"] for e in result["exposures"]]
            assert abs(sum(w for w in weights if w is not None) - 1.0) < 0.01
        finally:
            db.close()


class TestTopPositions:
    def test_top_positions_ranking(self):
        _reset_db()
        token = _register("top1@test.com")
        _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
        _add_transaction(token, "ETH", "crypto", 5.0, 2000.0)
        _add_transaction(token, "AAPL", "stock", 10.0, 150.0)

        db = SessionLocal()
        try:
            with _mock_prices({"BTC": 40000.0, "ETH": 2500.0, "AAPL": 180.0}):
                result = get_top_positions(db, 1)
            assert len(result) == 3
            assert result[0]["symbol"] == "BTC"
            assert result[1]["symbol"] == "ETH"
            assert result[2]["symbol"] == "AAPL"
        finally:
            db.close()

    def test_top_positions_limit(self):
        _reset_db()
        token = _register("top2@test.com")
        for i in range(7):
            sym = f"S{i}"
            _add_transaction(token, sym, "stock", 1.0, 10.0 * (i + 1))

        db = SessionLocal()
        try:
            prices = {f"S{i}": 100.0 * (i + 1) for i in range(7)}
            with _mock_prices(prices):
                result = get_top_positions(db, 1)
            assert len(result) == 5
        finally:
            db.close()

    def test_top_positions_empty(self):
        _reset_db()
        _register("top3@test.com")

        db = SessionLocal()
        try:
            result = get_top_positions(db, 1)
            assert result == []
        finally:
            db.close()


# ── API endpoint tests ──────────────────────────────────────────────


def test_allocation_endpoint_structure():
    _reset_db()
    token = _register("api1@test.com")
    _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)

    with _mock_prices({"BTC": 40000.0}):
        resp = client.get("/api/portfolio/allocation", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "total_value" in data
    assert "assets" in data
    assert len(data["assets"]) == 1
    asset = data["assets"][0]
    assert "symbol" in asset
    assert "quantity" in asset
    assert "price" in asset
    assert "value" in asset
    assert "weight" in asset


def test_allocation_endpoint_unauthenticated():
    resp = client.get("/api/portfolio/allocation")
    assert resp.status_code in (401, 403)


def test_exposure_endpoint_structure():
    _reset_db()
    token = _register("api2@test.com")
    _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
    _add_transaction(token, "AAPL", "stock", 10.0, 150.0)

    with _mock_prices({"BTC": 40000.0, "AAPL": 180.0}):
        resp = client.get("/api/portfolio/exposure", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "total_value" in data
    assert "exposures" in data
    for exp in data["exposures"]:
        assert "asset_class" in exp
        assert "value" in exp
        assert "weight" in exp


def test_exposure_endpoint_unauthenticated():
    resp = client.get("/api/portfolio/exposure")
    assert resp.status_code in (401, 403)


def test_top_positions_endpoint():
    _reset_db()
    token = _register("api3@test.com")
    _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
    _add_transaction(token, "ETH", "crypto", 5.0, 2000.0)

    with _mock_prices({"BTC": 40000.0, "ETH": 2500.0}):
        resp = client.get("/api/portfolio/top-positions", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "positions" in data
    assert len(data["positions"]) == 2
    assert data["positions"][0]["symbol"] == "BTC"


def test_top_positions_endpoint_unauthenticated():
    resp = client.get("/api/portfolio/top-positions")
    assert resp.status_code in (401, 403)


def test_allocation_user_isolation():
    _reset_db()
    token1 = _register("iso1@test.com")
    token2 = _register("iso2@test.com")
    _add_transaction(token1, "BTC", "crypto", 1.0, 30000.0)
    _add_transaction(token2, "AAPL", "stock", 10.0, 150.0)

    with _mock_prices({"BTC": 40000.0}):
        resp1 = client.get("/api/portfolio/allocation", headers=_auth(token1))
    with _mock_prices({"AAPL": 180.0}):
        resp2 = client.get("/api/portfolio/allocation", headers=_auth(token2))

    assert len(resp1.json()["assets"]) == 1
    assert resp1.json()["assets"][0]["symbol"] == "BTC"
    assert len(resp2.json()["assets"]) == 1
    assert resp2.json()["assets"][0]["symbol"] == "AAPL"


def test_weight_normalization():
    _reset_db()
    token = _register("norm@test.com")
    _add_transaction(token, "BTC", "crypto", 1.0, 30000.0)
    _add_transaction(token, "AAPL", "stock", 10.0, 150.0)
    _add_transaction(token, "ETH", "crypto", 5.0, 2000.0)

    with _mock_prices({"BTC": 40000.0, "AAPL": 180.0, "ETH": 2500.0}):
        resp = client.get("/api/portfolio/allocation", headers=_auth(token))
    data = resp.json()
    weights = [a["weight"] for a in data["assets"]]
    assert abs(sum(w for w in weights if w is not None) - 1.0) < 0.01
