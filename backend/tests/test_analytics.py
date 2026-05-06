from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app
from app.services import portfolio_analytics

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


# ── Overview Tests ───────────────────────────────────────────────────


@patch("app.services.portfolio_analytics.get_current_prices_map", side_effect=_mock_prices_map)
@patch("app.services.portfolio_analytics.get_latest_quotes")
def test_overview_empty_portfolio(mock_quotes, mock_prices):
    _reset_db()
    mock_quotes.return_value = []
    token = _register("analytics1@test.com")
    resp = client.get("/api/analytics/portfolio/overview", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_value"] == 0.0
    assert data["total_cost_basis"] == 0.0
    assert data["total_pnl"] == 0.0
    assert data["top_gainers"] == []
    assert data["top_losers"] == []


@patch("app.services.portfolio_analytics.get_current_prices_map", side_effect=_mock_prices_map)
@patch("app.services.portfolio_analytics.get_latest_quotes")
def test_overview_with_positions(mock_quotes, mock_prices):
    _reset_db()
    from app.schemas.market_data import MarketQuote
    from datetime import datetime, timezone

    mock_quotes.return_value = [
        MarketQuote(symbol="BTC", name="Bitcoin", price=65000, change=500, change_percent=2.0, updated_at=datetime.now(timezone.utc)),
        MarketQuote(symbol="ETH", name="Ethereum", price=3200, change=-50, change_percent=-1.5, updated_at=datetime.now(timezone.utc)),
    ]

    token = _register("analytics2@test.com")
    _add_txn(token, "BTC", "crypto", "buy", 1.0, 60000)
    _add_txn(token, "ETH", "crypto", "buy", 10.0, 3000)

    resp = client.get("/api/analytics/portfolio/overview", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_value"] == 97000.0  # 1*65000 + 10*3200
    assert data["total_cost_basis"] == 90000.0  # 1*60000 + 10*3000
    assert data["total_pnl"] == 7000.0

    assert len(data["allocation_by_symbol"]) == 2
    assert "BTC" in data["allocation_by_symbol"]
    assert "ETH" in data["allocation_by_symbol"]

    assert "crypto" in data["allocation_by_asset_type"]
    assert data["allocation_by_asset_type"]["crypto"] == 100.0


@patch("app.services.portfolio_analytics.get_current_prices_map", side_effect=_mock_prices_map)
@patch("app.services.portfolio_analytics.get_latest_quotes")
def test_overview_gainers_and_losers(mock_quotes, mock_prices):
    _reset_db()
    from app.schemas.market_data import MarketQuote
    from datetime import datetime, timezone

    mock_quotes.return_value = [
        MarketQuote(symbol="BTC", name="Bitcoin", price=65000, change=5000, change_percent=5.0, updated_at=datetime.now(timezone.utc)),
        MarketQuote(symbol="ETH", name="Ethereum", price=3200, change=-50, change_percent=-1.5, updated_at=datetime.now(timezone.utc)),
    ]

    token = _register("analytics3@test.com")
    _add_txn(token, "BTC", "crypto", "buy", 1.0, 60000)
    _add_txn(token, "ETH", "crypto", "buy", 10.0, 3500)

    resp = client.get("/api/analytics/portfolio/overview", headers=_auth(token))
    data = resp.json()

    assert len(data["top_gainers"]) >= 1
    assert data["top_gainers"][0]["symbol"] == "BTC"
    assert len(data["top_losers"]) >= 1
    assert data["top_losers"][0]["symbol"] == "ETH"


# ── Allocation Tests ─────────────────────────────────────────────────


@patch("app.services.portfolio_analytics.get_current_prices_map", side_effect=_mock_prices_map)
@patch("app.services.portfolio_analytics.get_latest_quotes")
def test_allocation_endpoint(mock_quotes, mock_prices):
    _reset_db()
    from app.schemas.market_data import MarketQuote
    from datetime import datetime, timezone

    mock_quotes.return_value = [
        MarketQuote(symbol="BTC", name="Bitcoin", price=65000, change=0, change_percent=0, updated_at=datetime.now(timezone.utc)),
    ]

    token = _register("analytics4@test.com")
    _add_txn(token, "BTC", "crypto", "buy", 1.0, 60000)

    resp = client.get("/api/analytics/portfolio/allocation", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["allocation_by_symbol"]["BTC"] == 100.0
    assert data["allocation_by_asset_type"]["crypto"] == 100.0


@patch("app.services.portfolio_analytics.get_current_prices_map", side_effect=_mock_prices_map)
@patch("app.services.portfolio_analytics.get_latest_quotes")
def test_allocation_mixed_assets(mock_quotes, mock_prices):
    _reset_db()
    from app.schemas.market_data import MarketQuote
    from datetime import datetime, timezone

    mock_quotes.return_value = [
        MarketQuote(symbol="BTC", name="Bitcoin", price=65000, change=0, change_percent=0, updated_at=datetime.now(timezone.utc)),
        MarketQuote(symbol="AAPL", name="Apple", price=190, change=0, change_percent=0, updated_at=datetime.now(timezone.utc)),
    ]

    token = _register("analytics5@test.com")
    _add_txn(token, "BTC", "crypto", "buy", 1.0, 60000)
    _add_txn(token, "AAPL", "stock", "buy", 100.0, 180)

    resp = client.get("/api/analytics/portfolio/allocation", headers=_auth(token))
    data = resp.json()

    assert "crypto" in data["allocation_by_asset_type"]
    assert "stock" in data["allocation_by_asset_type"]
    total_pct = sum(data["allocation_by_asset_type"].values())
    assert abs(total_pct - 100.0) < 0.1


# ── History Tests ────────────────────────────────────────────────────


def test_history_empty_portfolio():
    _reset_db()
    token = _register("analytics6@test.com")
    resp = client.get("/api/analytics/portfolio/history?range=1m", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["range"] == "1m"
    assert data["data"] == []


def test_history_with_positions():
    _reset_db()
    token = _register("analytics7@test.com")
    _add_txn(token, "BTC", "crypto", "buy", 1.0, 60000)

    resp = client.get("/api/analytics/portfolio/history?range=1m", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["range"] == "1m"
    assert len(data["data"]) == 30
    for point in data["data"]:
        assert "timestamp" in point
        assert "value" in point
        assert point["value"] > 0


def test_history_range_3m():
    _reset_db()
    token = _register("analytics8@test.com")
    _add_txn(token, "ETH", "crypto", "buy", 5.0, 3000)

    resp = client.get("/api/analytics/portfolio/history?range=3m", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["range"] == "3m"
    assert len(data["data"]) == 90


def test_history_invalid_range():
    _reset_db()
    token = _register("analytics9@test.com")
    resp = client.get("/api/analytics/portfolio/history?range=2w", headers=_auth(token))
    assert resp.status_code == 422


# ── Auth Tests ───────────────────────────────────────────────────────


def test_unauthenticated_requests_rejected():
    resp_overview = client.get("/api/analytics/portfolio/overview")
    resp_alloc = client.get("/api/analytics/portfolio/allocation")
    resp_history = client.get("/api/analytics/portfolio/history")
    assert resp_overview.status_code == 403
    assert resp_alloc.status_code == 403
    assert resp_history.status_code == 403


# ── User Isolation ───────────────────────────────────────────────────


@patch("app.services.portfolio_analytics.get_current_prices_map", side_effect=_mock_prices_map)
@patch("app.services.portfolio_analytics.get_latest_quotes")
def test_user_isolation(mock_quotes, mock_prices):
    _reset_db()
    from app.schemas.market_data import MarketQuote
    from datetime import datetime, timezone

    mock_quotes.return_value = [
        MarketQuote(symbol="BTC", name="Bitcoin", price=65000, change=0, change_percent=0, updated_at=datetime.now(timezone.utc)),
    ]

    token_a = _register("analytics_a@test.com")
    token_b = _register("analytics_b@test.com")

    _add_txn(token_a, "BTC", "crypto", "buy", 2.0, 60000)

    resp_a = client.get("/api/analytics/portfolio/overview", headers=_auth(token_a))
    resp_b = client.get("/api/analytics/portfolio/overview", headers=_auth(token_b))

    assert resp_a.json()["total_value"] == 130000.0
    assert resp_b.json()["total_value"] == 0.0
