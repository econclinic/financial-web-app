# PROJECT_CONTEXT.md

> A quick-reference guide for developers and AI agents working on this repository.

---

## 1. Overview

**AI Finance WebApp** is a modular financial web application that provides a dashboard for viewing market data, managing authentication, and tracking portfolios with real-time prices.

- **Typical user:** A retail investor or finance enthusiast who wants a single dashboard to monitor prices, manage a watchlist, and analyse market trends.
- **Current maturity:** Early MVP. The app has JWT-based authentication, real-time crypto prices (CoinGecko), mock stock data, a portfolio module for recording transactions and tracking positions with live P&L, a watchlist, and price alerts with a background trigger worker. There is no real brokerage integration or production database yet.

---

## 2. Tech Stack

### Backend

| Component | Details |
|---|---|
| Framework | FastAPI 0.115 (Python) |
| Server | Uvicorn 0.34 |
| ORM | SQLAlchemy 2.0 |
| Database (MVP) | SQLite (`finance.db`, auto-created on startup) |
| Database (production) | PostgreSQL 16 (via Docker Compose) |
| Auth | python-jose (JWT, HS256) + passlib/bcrypt |
| Validation | Pydantic 2.11 + pydantic-settings |
| Migrations | Alembic 1.15 (configured, not yet used) |
| HTTP client | httpx 0.28 (used for CoinGecko API calls) |

### Frontend

| Component | Details |
|---|---|
| Framework | Next.js 16.2 (App Router, TypeScript) |
| React | 19.2 |
| Styling | Tailwind CSS v4 |
| Component library | shadcn/ui (backed by @base-ui/react) |
| Icons | Lucide React |
| Charts | Recharts 3.8 |
| Fonts | Geist Sans + Geist Mono (via `next/font/google`) |

### Infrastructure

| Component | Details |
|---|---|
| Container orchestration | Docker Compose (`docker-compose.yml`) |
| Services | `db` (PostgreSQL 16-alpine), `backend` (FastAPI), `frontend` (Next.js) |
| Environment variables | `.env` file loaded by both backend (pydantic-settings) and Docker Compose; see `.env.example` |

---

## 3. High-level Architecture

```
Browser (port 3000)
   │
   │  REST / JSON
   ▼
Next.js Frontend  ──────►  FastAPI Backend (port 8000)
   │                            │
   │  AuthContext (JWT)         │  SQLAlchemy ORM
   │  localStorage              │
   ▼                            ▼
Protected Routes            SQLite (MVP) / PostgreSQL (prod)
```

- **Communication:** The frontend calls the backend over REST (JSON). Auth uses JWT Bearer tokens sent in the `Authorization` header.
- **Monorepo structure:** Two top-level directories — `backend/` and `frontend/` — each with their own Dockerfile. They share a root `docker-compose.yml` and `.env.example`.
- **Configuration:** The backend reads settings from environment variables (or `.env`) via `pydantic-settings` (`backend/app/core/config.py`). The frontend reads `NEXT_PUBLIC_API_BASE_URL` at build/runtime. Defaults are set for local development so the app runs without a `.env` file.

---

## 4. Implemented Modules

### 4.1 Auth Module

**Backend endpoints** (prefix: `/api/auth`):

| Method | Route | Description | Auth required |
|---|---|---|---|
| POST | `/api/auth/register` | Create a new user (hashes password with bcrypt, stores in DB). Returns `UserResponse`. Returns 409 if email already exists. | No |
| POST | `/api/auth/login` | Verify email + password. Returns `TokenResponse` with a JWT access token (1 h expiry). Returns 401 on invalid credentials. | No |
| GET | `/api/auth/me` | Return the current user's `id` and `email`. | Yes (Bearer token) |

**JWT behaviour:**
- Algorithm: HS256.
- `sub` claim: the user's integer `id` cast to a string.
- Expiry: 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).
- Signing key: `SECRET_KEY` (must be changed for production).

**Password hashing:** bcrypt via `passlib.context.CryptContext`.

**Frontend pages and route protection:**
- `/login` — email/password sign-in form. Errors shown in a red banner.
- `/register` — email/password/confirm form. Auto-logs in on success.
- `/` (dashboard) — wrapped in `<ProtectedRoute>`, redirects to `/login` if no valid token.
- `<Navbar>` — shows Login/Register links when logged out; shows email + Logout button when logged in.
- `<AuthProvider>` (context) wraps the app in `layout.tsx`. Token is stored in `localStorage` under the key `auth_token` and restored on page load.

**Key files:**

```
backend/app/api/v1/endpoints/auth.py   # Route handlers
backend/app/core/security.py           # hash/verify password, create/decode JWT
backend/app/core/deps.py               # get_current_user dependency (HTTPBearer)
backend/app/models/user.py             # SQLAlchemy User model
backend/app/schemas/auth.py            # Pydantic request/response models
backend/app/services/auth.py           # Business logic (create user, authenticate)

frontend/src/hooks/use-auth.tsx         # AuthProvider + useAuth hook
frontend/src/lib/auth.ts                # API client (register, login, fetchCurrentUser)
frontend/src/app/login/page.tsx         # Login page
frontend/src/app/register/page.tsx      # Register page
frontend/src/components/shared/protected-route.tsx
frontend/src/components/shared/navbar.tsx
```

**Extending the auth module:**
- Add password-reset or email-verification flows by creating new endpoints in `auth.py` and corresponding frontend pages.
- Protect additional endpoints by adding `Depends(get_current_user)` to their route handlers.
- Switch to a production database by changing `SQLITE_URL` to a PostgreSQL connection string.

---

### 4.2 Market Data Module (Live + Mock)

**Data sources:**
- **Crypto (BTC, ETH):** Real-time prices from [CoinGecko](https://www.coingecko.com/en/api) public API (no API key required). Includes 24-hour price change percentage.
- **Stocks (AAPL):** Mock data with deterministic jitter (`seed=42`). Will be replaced with a real provider in the future.

**Caching strategy:**
- Prices are cached in-memory for 60 seconds to avoid CoinGecko rate limits.
- On API failure, the last cached price is returned if available.
- If no cache exists and the API is down, a 503 error is returned with a clear message.

**Symbol mapping (internal → CoinGecko):** `BTC` → `bitcoin`, `ETH` → `ethereum`.

**Backend endpoints:**

| Method | Route | Description | Auth required |
|---|---|---|---|
| GET | `/api/market-data/latest` | Returns current quotes for all symbols (real for crypto, mock for stocks). | No |
| GET | `/api/market-data/history?symbol=BTC&days=30` | Returns daily mock price points for a symbol. Returns 404 for unknown symbols. `days` defaults to 30 (max 365). | No |
| GET | `/api/market/prices?symbols=BTC,ETH` | Returns live prices for requested symbols. Response: `{"BTC": {"price": 62000, "change_24h": -0.25}, ...}` | Yes (Bearer token) |

**Frontend components:**
- `<MarketDataSection>` — orchestrates price cards and chart.
- `<PriceCard>` — shows symbol name, price, daily change with green/red colour coding. Clicking a card selects the symbol.
- `<PriceChart>` — 30-day line chart rendered with Recharts for the selected symbol.
- Portfolio positions table shows a green **"Live"** badge next to current prices sourced from CoinGecko.

**Key files:**

```
backend/app/api/v1/endpoints/market_data.py    # Dashboard quote/history routes
backend/app/api/v1/endpoints/market.py         # GET /api/market/prices (auth required)
backend/app/services/market_data_service.py    # CoinGecko integration, caching, fallback
backend/app/services/market_data.py            # Orchestrates live + mock data for dashboard
backend/app/schemas/market_data.py             # Pydantic models (MarketQuote, PricePoint)

frontend/src/components/shared/market-data-section.tsx
frontend/src/components/shared/price-card.tsx
frontend/src/components/shared/price-chart.tsx
frontend/src/lib/market-data.ts                # API client for market data
frontend/src/lib/portfolio.ts                  # fetchMarketPrices() for live price endpoint
```

**Future extension:**
- Add real stock price providers (Alpha Vantage, Yahoo Finance) for AAPL and other equities.
- Add WebSocket support for real-time price streaming.
- Replace mock price history with real historical data from CoinGecko `/coins/{id}/market_chart` endpoint.
- Protect dashboard market data endpoints with `Depends(get_current_user)` if desired.

---

### 4.3 Portfolio Module

**Backend endpoints** (prefix: `/api/portfolio`):

| Method | Route | Description | Auth required |
|---|---|---|---|
| POST | `/api/portfolio/transactions` | Record a new buy or sell transaction. Validates that sell quantity does not exceed owned quantity. | Yes (Bearer token) |
| GET | `/api/portfolio/transactions` | List all transactions for the current user (newest first). | Yes (Bearer token) |
| GET | `/api/portfolio/summary` | Return portfolio summary: total value, total invested, total P&L, and per-symbol positions with unrealized P&L. | Yes (Bearer token) |

**Database model — `PortfolioTransaction`:**

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `user_id` | Integer | FK to User (not enforced at DB level for SQLite compatibility) |
| `symbol` | String | e.g. BTC, ETH, AAPL |
| `asset_type` | Enum(`crypto`, `stock`) | Asset classification |
| `transaction_type` | Enum(`buy`, `sell`) | Direction |
| `quantity` | Float | Must be > 0 |
| `price` | Float | Must be > 0 |
| `timestamp` | DateTime (UTC) | Defaults to now |

**Business logic (positions are calculated dynamically, no separate table):**
- Position quantity = sum of buys − sum of sells per symbol.
- Average buy price = weighted average of all buy transactions.
- Current price fetched from the Market Data service (live CoinGecko prices for crypto, mock for stocks).
- Unrealized P&L = (current_price − avg_buy_price) × quantity.

**Validation rules:**
- Cannot sell more than the currently owned quantity.
- Quantity and price must be > 0.
- All endpoints require JWT authentication.

**Frontend pages:**
- `/portfolio` — Protected page showing summary cards (Total Value, Total Invested, P&L, Return %), positions table with "Live" price badges, portfolio allocation chart (Recharts), and transaction history table. Shows a spinner during loading and a yellow warning banner if live prices are temporarily unavailable.
- `/portfolio/new-transaction` — Form to record a new transaction with symbol selector, asset type, transaction type, quantity, and price fields. Redirects to `/portfolio` on success.
- Navbar shows a "Portfolio" button when authenticated.

**Key files:**

```
backend/app/api/v1/endpoints/portfolio.py   # Route handlers
backend/app/models/portfolio.py             # PortfolioTransaction model
backend/app/schemas/portfolio.py            # Pydantic request/response models
backend/app/services/portfolio.py           # Position calculation, validation

frontend/src/app/portfolio/page.tsx                   # Portfolio dashboard
frontend/src/app/portfolio/new-transaction/page.tsx   # New transaction form
frontend/src/lib/portfolio.ts                         # API client for portfolio
```

**Extending the portfolio module:**
- Add support for more symbols by extending the market data service.
- Add transaction editing and deletion endpoints.
- Add historical portfolio value tracking over time.
- Connect to a real brokerage API for automatic transaction import.

---

### 4.4 Watchlist Module

**Backend endpoints** (prefix: `/api/watchlist`):

| Method | Route | Description | Auth required |
|---|---|---|---|
| GET | `/api/watchlist` | Return the current user's watchlist items (newest first). | Yes (Bearer token) |
| POST | `/api/watchlist` | Add a symbol to the user's watchlist. Normalises to uppercase. Returns 409 if the symbol is already in the watchlist. | Yes (Bearer token) |
| DELETE | `/api/watchlist/{symbol}` | Remove a symbol from the user's watchlist. Returns 404 if not found. | Yes (Bearer token) |

**Database model — `WatchlistItem`:**

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `user_id` | Integer | FK to User (logical, not enforced at DB level for SQLite compatibility) |
| `symbol` | String | Stored as uppercase |
| `created_at` | DateTime (UTC) | Defaults to now |

**Constraints:** Unique index on `(user_id, symbol)` — each user can only add a symbol once.

**Business logic:**
- Symbols are normalised to uppercase before storage and comparison.
- Duplicate detection is handled by the database unique constraint; the service catches `IntegrityError` and the endpoint returns HTTP 409.
- Users can only see and modify their own watchlist (user isolation enforced in all queries).

**Frontend page:**
- `/watchlist` — Protected page showing the user's watchlist in a table with columns: Symbol, Current Price (fetched via existing market data service), 24h Change, and a Remove button. Includes an input + Add button at the top for adding new symbols. Shows loading spinner, error banner, and an empty state with guidance.
- Navbar shows a "Watchlist" button (with eye icon) when authenticated.

**Key files:**

```
backend/app/api/v1/endpoints/watchlist.py   # Route handlers (GET, POST, DELETE)
backend/app/models/watchlist.py             # WatchlistItem ORM model
backend/app/schemas/watchlist.py            # WatchlistAdd, WatchlistResponse
backend/app/services/watchlist.py           # get_user_watchlist, add_symbol, remove_symbol
backend/tests/test_watchlist.py             # pytest tests (7 tests)

frontend/src/app/watchlist/page.tsx         # Watchlist page
frontend/src/lib/watchlist.ts               # API client (fetchWatchlist, addToWatchlist, removeFromWatchlist)
```

**Test coverage (pytest):**
- Retrieve empty watchlist
- Add symbol (normalised to uppercase)
- Prevent duplicate symbols (HTTP 409)
- Delete symbol
- Delete missing symbol (HTTP 404)
- Reject unauthenticated requests (HTTP 403)
- User isolation (user A cannot see or delete user B's symbols)

**Extending the watchlist module:**
- Add notes or tags per watchlist entry.
- Add a "quick add to portfolio" flow from the watchlist.

---

### 4.5 Price Alerts Module

**Backend endpoints** (prefix: `/api/alerts`):

| Method | Route | Description | Auth required |
|---|---|---|---|
| GET | `/api/alerts` | Return the current user's alerts (newest first). | Yes (Bearer token) |
| POST | `/api/alerts` | Create a new price alert. Normalises symbol to uppercase. Returns 409 if an identical active alert already exists. | Yes (Bearer token) |
| DELETE | `/api/alerts/{id}` | Delete a specific alert belonging to the current user. Returns 404 if not found. | Yes (Bearer token) |

**Database model — `Alert`:**

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `user_id` | Integer | FK to User (logical) |
| `symbol` | String | Stored as uppercase |
| `target_price` | Float | Must be > 0 |
| `direction` | String | `"above"` or `"below"` |
| `is_triggered` | Boolean | Defaults to `false` |
| `created_at` | DateTime (UTC) | Defaults to now |
| `triggered_at` | DateTime (UTC) | Nullable; set when alert fires |

**Constraints:** Unique index on `(user_id, symbol, direction, target_price, is_triggered)` — prevents duplicate active alerts with the same parameters.

**Business logic:**
- Symbols are normalised to uppercase before storage.
- Duplicate active-alert detection is handled by the database unique constraint; the service catches `IntegrityError` and the endpoint returns HTTP 409.
- Users can only see and modify their own alerts (user isolation enforced in all queries).

**Background worker:**
- An asyncio background task runs every 60 seconds.
- Fetches live prices from the existing Market Data service (CoinGecko for crypto, mock for stocks).
- Evaluates all active (`is_triggered=false`) alerts:
  - `direction="above"`: triggers if current price ≥ target price.
  - `direction="below"`: triggers if current price ≤ target price.
- Once triggered, `is_triggered` is set to `true` and `triggered_at` is recorded. The alert does not fire again.
- Designed to be extensible — add new periodic tasks to `_run_tasks()` in `background.py`.

**Frontend page:**
- `/alerts` — Protected page showing alerts in a table with columns: Symbol, Condition (Above/Below $X), Status (Active/Triggered badge), Triggered At timestamp, and a Delete button. Triggered rows are highlighted with a green background.
- Form with symbol selector (BTC, ETH, AAPL), direction selector (Above/Below), target price input, and "Create Alert" button.
- Navbar shows an "Alerts" button (with bell icon) when authenticated.

**Key files:**

```
backend/app/api/v1/endpoints/alerts.py    # Route handlers (GET, POST, DELETE)
backend/app/models/alert.py              # Alert ORM model
backend/app/schemas/alert.py             # AlertCreate, AlertResponse
backend/app/services/alerts.py           # CRUD + evaluate_alerts trigger logic
backend/app/services/background.py       # Async background worker (60s interval)
backend/tests/test_alerts.py             # pytest tests (11 tests)

frontend/src/app/alerts/page.tsx         # Alerts page
frontend/src/lib/alerts.ts               # API client (fetchAlerts, createAlert, deleteAlert)
```

**Test coverage (pytest):**
- Retrieve empty alerts list
- Create alert (normalised to uppercase)
- Prevent duplicate active alerts (HTTP 409)
- Delete alert
- Delete nonexistent alert (HTTP 404)
- Reject unauthenticated requests (HTTP 403)
- User isolation (user A cannot delete user B's alerts)
- Trigger logic — above direction (fires when price ≥ target)
- Trigger logic — below direction (fires when price ≤ target)
- No trigger when condition not met
- Triggered alert does not fire again

**Extending the alerts module:**
- Add email or push notification channels when alerts fire.
- Add recurring alerts (re-arm after trigger).

---

### 4.6 Notifications System (MVP)

**Overview:**
In-app notification system triggered by the Price Alerts module. When a price alert triggers, a notification is automatically created for the user. Users can view, mark as read (single or all), and see an unread badge in the navbar.

**Backend endpoints** (prefix: `/api/notifications`):

| Method | Route | Description | Auth required |
|---|---|---|---|
| GET | `/api/notifications` | Return user notifications, newest first. Supports `limit` and `offset` query params. | Yes (Bearer token) |
| GET | `/api/notifications/unread-count` | Return `{ unread_count: N }` for navbar badge. | Yes (Bearer token) |
| POST | `/api/notifications/{id}/read` | Mark a single notification as read. Returns 404 if not found or not owned. | Yes (Bearer token) |
| POST | `/api/notifications/read-all` | Mark all unread notifications as read for the current user. | Yes (Bearer token) |

**Database model — `Notification`:**

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `user_id` | Integer | FK to `users.id` |
| `type` | String | e.g. `"price_alert_triggered"` |
| `title` | String | e.g. `"Alert Triggered"` |
| `message` | String | e.g. `"BTC crossed above 70000"` |
| `is_read` | Boolean | Defaults to `false` |
| `related_alert_id` | Integer (nullable) | FK to `alerts.id` |
| `created_at` | DateTime (UTC) | Defaults to now |

**Integration with Price Alerts:**
- When the background worker triggers an alert, exactly one notification is created.
- Duplicate prevention: checks if a notification with `related_alert_id` and `type="price_alert_triggered"` already exists before creating.
- Message format: `"{SYMBOL} crossed above {price}"` or `"{SYMBOL} dropped below {price}"`.

**Frontend:**
- `/notifications` — Protected page listing notifications with read/unread visual distinction, "Mark as read" per item, and "Mark all as read" button.
- Navbar shows a "Notifications" button with a red unread count badge (polls every 30s). Uses `BellRing` icon when unread > 0.

**Key files:**

```
backend/app/api/v1/endpoints/notifications.py  # Route handlers
backend/app/models/notification.py             # Notification ORM model
backend/app/schemas/notification.py            # NotificationResponse, UnreadCountResponse
backend/app/services/notifications.py          # CRUD + unread count
backend/tests/test_notifications.py            # pytest tests (12 tests)

frontend/src/app/notifications/page.tsx        # Notifications page
frontend/src/lib/notifications.ts              # API client
```

**Test coverage (pytest):**
- Retrieve empty notifications list
- Create and list notifications (ordering)
- Pagination (limit/offset)
- Mark single notification as read
- Mark nonexistent notification (HTTP 404)
- Mark all as read
- Unread count accuracy
- User isolation (no cross-user access)
- Reject unauthenticated requests (HTTP 403)
- Notification created on alert trigger (above)
- Notification created on alert trigger (below)
- No duplicate notification on repeated triggers

**Future extensions:**
- Email or push notification channels.
- Notification preferences (opt-in/out per type).
- Real-time delivery via WebSocket.

---

## 5. Repository Structure

```
financial-web-app/
├── .env.example                      # Environment variable template
├── .gitignore
├── docker-compose.yml                # PostgreSQL + backend + frontend services
├── PROJECT_CONTEXT.md                # This file
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                   # FastAPI app, lifespan, CORS, router includes
│       ├── api/
│       │   └── v1/
│       │       ├── router.py         # Versioned API router (health)
│       │       └── endpoints/
│       │           ├── health.py     # GET /api/v1/health
│       │           ├── auth.py       # POST register, login; GET me
│       │           ├── market_data.py# GET latest, history
│       │           ├── market.py     # GET /api/market/prices (live, auth required)
│       │           ├── portfolio.py  # POST/GET transactions, GET summary
│       │           ├── watchlist.py  # GET/POST/DELETE watchlist
│       │           └── alerts.py    # GET/POST/DELETE alerts
│       ├── core/
│       │   ├── config.py            # Settings (pydantic-settings)
│       │   ├── database.py          # SQLAlchemy engine, session, Base
│       │   ├── deps.py              # get_current_user dependency
│       │   └── security.py          # JWT + password hashing utilities
│       ├── models/
│       │   ├── user.py              # User ORM model
│       │   ├── portfolio.py         # PortfolioTransaction ORM model
│       │   ├── watchlist.py         # WatchlistItem ORM model
│       │   └── alert.py            # Alert ORM model
│       ├── schemas/
│       │   ├── auth.py              # UserRegister, UserLogin, UserResponse, TokenResponse
│       │   ├── market_data.py       # MarketQuote, PricePoint, response wrappers
│       │   ├── portfolio.py         # TransactionCreate, PositionResponse, PortfolioSummaryResponse
│       │   ├── watchlist.py         # WatchlistAdd, WatchlistResponse
│       │   └── alert.py            # AlertCreate, AlertResponse
│       └── services/
│           ├── auth.py              # create_user, authenticate_user, get_user_by_email
│           ├── market_data_service.py # CoinGecko integration, 60s cache, fallback
│           ├── market_data.py       # Orchestrates live + mock quote/history
│           ├── portfolio.py         # Position calculation, validation, P&L
│           ├── watchlist.py         # Watchlist CRUD operations
│           ├── alerts.py           # Alert CRUD + trigger evaluation
│           └── background.py       # Async background worker (60s alert checker)
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── next.config.ts
    ├── tsconfig.json
    ├── components.json               # shadcn/ui configuration
    └── src/
        ├── app/
        │   ├── layout.tsx            # Root layout (AuthProvider, fonts, metadata)
        │   ├── page.tsx              # Dashboard (protected)
        │   ├── login/page.tsx        # Login page
        │   ├── register/page.tsx     # Register page
        │   ├── portfolio/
        │   │   ├── page.tsx          # Portfolio dashboard (positions, summary, chart)
        │   │   └── new-transaction/
        │   │       └── page.tsx      # New transaction form
        │   ├── watchlist/
        │   │   └── page.tsx          # Watchlist page
        │   └── alerts/
        │       └── page.tsx          # Price alerts page
        ├── components/
        │   ├── ui/
        │   │   └── button.tsx        # shadcn Button (base-ui)
        │   └── shared/
        │       ├── navbar.tsx
        │       ├── protected-route.tsx
        │       ├── market-data-section.tsx
        │       ├── price-card.tsx
        │       └── price-chart.tsx
        ├── hooks/
        │   └── use-auth.tsx          # AuthProvider + useAuth context
        └── lib/
            ├── api.ts                # Base API client utility
            ├── auth.ts               # Auth API functions
            ├── market-data.ts        # Market data API functions
            ├── portfolio.ts          # Portfolio API functions
            ├── watchlist.ts          # Watchlist API functions
            ├── alerts.ts            # Alerts API functions
            └── utils.ts              # cn() helper (tailwind-merge + clsx)
```

---

## 6. Development Workflow

### Branch strategy

- **`main` is protected.** Never commit directly to it.
- Create a feature branch for each piece of work (e.g. `feat/portfolio-module`, `fix/login-redirect`).
- Push the branch and open a Pull Request. Merge only after review.

### Local development

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

The backend auto-creates `finance.db` on startup. Delete the file to reset the database.

### Docker (optional)

```bash
cp .env.example .env          # adjust SECRET_KEY for production
docker compose up --build
```

This starts PostgreSQL, backend (port 8000), and frontend (port 3000).

### Continuous Integration (GitHub Actions)

CI runs automatically on every **push to `main`** and on every **pull request targeting `main`**. The workflow is defined in `.github/workflows/ci.yml` and contains two parallel jobs:

| Job | Runner | Steps |
|---|---|---|
| **Backend** | Python 3.11 | Install deps → `ruff check app/` (lint) → `pytest tests/ -v` (tests) |
| **Frontend** | Node 20 | `npm ci` → `npm run lint` (ESLint) → `npm run build` (production build) |

Both jobs use caching (`pip` and `npm`) to speed up repeat runs. The jobs run in parallel — the full CI pipeline typically finishes in under 2 minutes.

**Viewing CI logs:**
1. Open the Pull Request on GitHub.
2. Scroll to the status checks section at the bottom.
3. Click **"Details"** next to a failed or passed job to see its full log output.
4. Alternatively, go to the repository's **Actions** tab to see all workflow runs.

**Dev dependencies:** Backend linting and testing tools are in `requirements-dev.txt` (ruff, pytest). Install them locally with `pip install -r requirements-dev.txt`.

### For AI agents

1. **Read `PROJECT_CONTEXT.md` first** before making any changes.
2. Read `AI_DEVELOPMENT_GUIDE.md` if it exists.
3. Read `frontend/AGENTS.md` — Next.js 16 has breaking changes from common training data.
4. Always work on a feature branch; never commit to `main`.
5. GitHub is the single source of truth.

---

## 7. Roadmap / Next Steps

| Priority | Feature | Status | Description |
|---|---|---|---|
| 1 | Portfolio Module | Done | Record transactions, view positions, P&L, and allocation chart. |
| 2 | Watchlist | Done | Track favourite symbols with live prices. Add/remove symbols, duplicate prevention, user isolation. |
| 3 | Real Market Data Providers | Partial | CoinGecko integrated for crypto (BTC, ETH). Stock prices (AAPL) still mock — need Alpha Vantage or Yahoo Finance. |
| 4 | Economic Calendar | Planned | Surface upcoming earnings, FOMC meetings, and macro data releases. |
| 5 | Price Alerts | Done | Simple one-time trigger alerts with background worker (60s). Triggered state visible in UI. |
| 5b | Notifications (MVP) | Done | In-app notifications triggered by price alerts. Read/unread state, navbar badge, dedicated page. |
| 6 | CI/CD Pipeline | Done | GitHub Actions CI with parallel backend (ruff + pytest) and frontend (ESLint + build) jobs. |
| 7 | AI Analysis Tools | Planned | Summarise trends, generate trade ideas, or score sentiment with LLMs. |
