# PROJECT_CONTEXT.md

> A quick-reference guide for developers and AI agents working on this repository.

---

## 1. Overview

**AI Finance WebApp** is a modular financial web application that provides a dashboard for viewing market data, managing authentication, and tracking portfolios with real-time prices.

- **Typical user:** A retail investor or finance enthusiast who wants a single dashboard to monitor prices, manage a watchlist, and analyse market trends.
- **Current maturity:** Completed MVP — Entering Product Professionalization Stage. The initial roadmap (Phases 1–7) is finished. The app has JWT-based authentication, real-time crypto prices (CoinGecko), mock stock data, a portfolio module with analytics dashboard, a watchlist, four alert rule types (price above/below, daily change above/below) with background trigger worker and in-app notifications, toast notifications, skeleton loaders, meaningful empty states, dark/light theme, bilingual i18n (EN/FA) with full RTL support, responsive mobile-first layouts, and a smart market insights card. The project is now entering Stage 3 — focused on product hardening, external integrations, branding, and infrastructure stabilization.

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
| Fonts | Inter + Vazirmatn + Geist Mono (via `next/font/google`) |
| i18n | Client-side only; `useLocale()` hook + localStorage (`app-locale`) |
| Theme | Dark/light; `useTheme()` hook + localStorage (`app-theme`) |

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
        │   ├── layout.tsx            # Root layout (ThemeProvider, LocaleProvider, AuthProvider, fonts, anti-FOUC script)
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
        │       ├── price-chart.tsx
        │       ├── theme-toggle.tsx       # Sun/Moon theme toggle
        │       ├── language-toggle.tsx    # Globe language toggle (EN ↔ FA)
        │       └── smart-summary-card.tsx # Market insights summary card
        ├── hooks/
        │   ├── use-auth.tsx          # AuthProvider + useAuth context
        │   ├── use-theme.tsx         # ThemeProvider + useTheme (useSyncExternalStore)
        │   └── use-locale.tsx        # LocaleProvider + useLocale (useSyncExternalStore)
        └── lib/
            ├── api.ts                # Base API client utility
            ├── auth.ts               # Auth API functions
            ├── market-data.ts        # Market data API functions
            ├── portfolio.ts          # Portfolio API functions
            ├── watchlist.ts          # Watchlist API functions
            ├── alerts.ts            # Alerts API functions
            ├── utils.ts              # cn() helper (tailwind-merge + clsx)
            └── i18n/
                └── translations.ts   # EN + FA dictionaries, t() helper, TranslationKey type
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

### 4.7 Portfolio Analytics Module

**Overview:**
The Portfolio Analytics module extends the existing Portfolio module by computing on-demand performance insights, allocation breakdowns, and historical value timeseries. No new database tables are created — all analytics are derived from existing portfolio transactions and current market prices.

**Backend endpoints** (prefix: `/api/analytics`):

| Method | Route | Description | Auth required |
|---|---|---|---|
| GET | `/api/analytics/portfolio/overview` | Returns total_value, total_cost_basis, total_pnl, today_change_value, today_change_percent, top_gainers, top_losers, allocation_by_asset_type, allocation_by_symbol | Yes |
| GET | `/api/analytics/portfolio/allocation` | Returns allocation_by_asset_type and allocation_by_symbol (suitable for pie charts) | Yes |
| GET | `/api/analytics/portfolio/history?range=1m\|3m\|6m\|1y\|all` | Returns timestamp/value timeseries for portfolio history | Yes |

**Calculation logic (`portfolio_analytics_service.py`):**
- `calculate_portfolio_overview()` — aggregates positions, fetches current prices and 24h quotes, computes total value, cost basis, P&L, today's change, allocation percentages, and ranks gainers/losers
- `calculate_allocation()` — returns allocation breakdowns (delegates to overview)
- `build_time_series_history()` — builds daily portfolio value timeseries using historical price data from the market data provider, multiplied by held quantities

**Formulas:**
- **Total Value:** Σ (net_quantity × current_price) for each held symbol
- **Cost Basis:** Σ (net_quantity × average_buy_price) — average buy price = total_buy_cost / total_buy_quantity
- **P&L:** total_value − total_cost_basis
- **Today's Change:** Σ (position_value × change_percent_24h / 100)
- **Allocation %:** position_value / total_value × 100

**Caching:**
Heavy computations are cached in-memory per user with a 5-minute TTL. Cache is keyed by `user_id` and stores the full overview result.

**Frontend page:** `/dashboard/analytics`
- **Overview Cards:** Total Value, Today's Change, Total P&L, Cost Basis
- **Allocation Pie Charts:** Two donut charts — by asset class and by symbol (Recharts)
- **Performance Line Chart:** Selectable timeframe (1M, 3M, 6M, 1Y, ALL) showing daily portfolio value
- **Top Movers:** Top 5 gainers and losers with color-coded P&L percentages

**Key files:**

```
backend/app/services/portfolio_analytics.py    # Analytics calculations + caching
backend/app/api/v1/endpoints/analytics.py      # API route handlers
backend/app/schemas/analytics.py               # Pydantic response models
backend/tests/test_analytics.py                # 11 pytest tests

frontend/src/lib/analytics.ts                  # API client
frontend/src/app/dashboard/analytics/page.tsx  # Analytics dashboard page
```

---

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

---

## UI/UX Transformation (Phases 1–5 Complete)

The app underwent a 7-phase UI/UX transformation delivered as isolated, sequential PRs. Each phase was a separate feature branch merged into `main` before the next began.

### Phase 1 — Design Tokens + Theme System (PR #12)
- Full dark/light theme via CSS custom properties (HSL-based design tokens in `globals.css`).
- Dark mode is default; theme persists in `localStorage` under key `app-theme`.
- Sun/Moon toggle button in navbar (uses `useTheme()` hook with `useSyncExternalStore`).
- Anti-FOUC inline script in `<head>` reads `app-theme` before React hydrates.

### Phase 2 — Typography + Font Loading (PR #13)
- **Inter** (Latin) and **Vazirmatn** (Arabic/Persian) loaded via `next/font/google`.
- Font stack: `Vazirmatn, Inter, ui-sans-serif, system-ui, sans-serif`.
- Heading font-family token `--font-heading` shares the same stack.
- Weights used: 400 (body), 500 (labels), 600 (headings/bold).
- Typography tokens applied globally in `@layer base` (h1–h4 sizes, line-heights, letter-spacing).

### Phase 3 — Responsive Layouts (PR #14)
- Mobile-first responsive grids across Dashboard, Analytics, Portfolio, Alerts, Watchlist.
- Mobile hamburger menu in navbar (hidden on `md:`+).
- Edge-to-edge tables on mobile with horizontal scroll.
- Consistent `container mx-auto px-4 sm:px-6` spacing pattern.

### Phase 4 — i18n + RTL Support (PR #15)
- **Languages:** English (EN) and Persian/Farsi (FA).
- Translation file: `frontend/src/lib/i18n/translations.ts` — 100+ flat dot-notation keys.
- `useLocale()` hook (mirrors `useTheme()` pattern with `useSyncExternalStore`).
- `LocaleProvider` wraps app; locale persists in `localStorage` under key `app-locale`.
- Globe icon toggle in navbar switches between EN ↔ FA.
- Dynamic `dir="rtl|ltr"` and `lang` attributes on `<html>`.
- Anti-FOUC inline script reads `app-locale` and sets `dir`/`lang` before hydration.
- RTL text alignment rules in `globals.css` (`html[dir="rtl"] { text-align: right }`).
- Directional spacing via Tailwind `ltr:`/`rtl:` variants where needed.
- All pages translated: Dashboard, Portfolio, Analytics, Alerts, Watchlist, Notifications, Auth.

**Key decisions:**
- No route-based i18n (no `[lang]` segment); locale is client-side only via localStorage.
- `overflow-x: clip` was initially used on `<html>` for RTL overflow prevention but was removed because it caused scroll clipping on some Chrome DevTools device presets (viewport overflow propagation issue). RTL horizontal overflow is instead handled by keeping content within viewport width via responsive utilities.

### Phase 5 — Smart Summary Card (PR #16)
- `SmartSummaryCard` component on the Dashboard showing real-time market insights:
  - **Avg. Daily Change:** Mean percentage change across all tracked assets (color-coded).
  - **Total absolute change:** Combined dollar change across all assets.
  - **Best Performer:** Asset with highest daily percentage gain.
  - **Worst Performer:** Asset with lowest daily percentage change.
- Responsive 3-column grid (stacks on mobile).
- `MarketDataSection` exposes quotes via `onQuotesLoaded` callback prop.
- 5 new i18n keys (EN + FA) under `summary.*` namespace.
- Card renders only after market data loads (no flash of empty state).

**Key files added during UI/UX transformation:**

```
frontend/src/hooks/use-theme.tsx                          # Theme state (useSyncExternalStore)
frontend/src/hooks/use-locale.tsx                         # Locale state (useSyncExternalStore)
frontend/src/components/shared/theme-toggle.tsx           # Sun/Moon toggle button
frontend/src/components/shared/language-toggle.tsx        # Globe toggle button (EN ↔ FA)
frontend/src/components/shared/smart-summary-card.tsx     # Market insights card
frontend/src/lib/i18n/translations.ts                     # EN + FA translation dictionaries
frontend/src/lib/benchmark-data.ts                        # Mock benchmark data (BTC, S&P 500)
```

### Phase 6 — Benchmark Comparison (PR #17)
- Benchmark selector on the Portfolio Performance chart: **None** (default), **BTC**, **S&P 500**.
- Amber-highlighted active state button; selector row sits between time range buttons and the chart.
- Benchmark rendered as a **dashed amber line** (`#f59e0b`, `strokeDasharray="6 3"`) — visually distinct from the solid blue portfolio line.
- **Normalization:** benchmark values are indexed to the portfolio's starting value so both lines share the same Y-axis scale, making relative performance directly comparable.
- **Legend** auto-appears when a benchmark is selected ("Portfolio" vs benchmark name).
- Mock data generated client-side via deterministic seeded PRNG (mulberry32, seeds 42/99) — BTC ~3% daily vol, S&P 500 ~0.8% daily vol. Replace `getBenchmarkData()` with a real API call when backend data is available; the chart component needs no changes.
- 3 new i18n keys (EN + FA): `analytics.benchmark`, `analytics.benchmarkNone`, `analytics.portfolio`.

**Key files:**
```
frontend/src/lib/benchmark-data.ts   # Mock benchmark data generator (BenchmarkId, getBenchmarkData, getBenchmarkLabel)
```

### Phase 7 — Alerts Upgrade + UX Polish (Done)

**Alert Rule Types:**
- Extended the alert system from simple above/below triggers to four rule types: `price_above`, `price_below`, `daily_change_above`, `daily_change_below`.
- Backend `evaluate_alerts()` now accepts an optional `changes` dict for 24h percentage data alongside prices.
- Background worker passes both price and 24h change data from `get_live_prices()`.
- Schema validation: price alerts require `target_price > 0`; daily change alerts allow negative targets (e.g. alert when daily change drops below -3%).
- Old `"above"`/`"below"` direction values are still evaluated correctly for backward compatibility.

**Toast Notifications:**
- Added `sonner` (via shadcn/ui) for non-intrusive, auto-dismissing toast feedback.
- Toasts shown on: alert created, alert deleted, theme changed, language changed.
- `<Toaster>` component mounted in root layout, positioned bottom-right, 3s auto-dismiss.

**Skeleton Loaders:**
- Dashboard: skeleton cards + chart placeholder during market data loading.
- Portfolio: skeleton stat cards + table rows during portfolio loading.
- Analytics: skeleton overview cards + chart placeholders during data loading.
- All skeletons use `animate-pulse` with `bg-muted` to match the existing design system.

**Empty States:**
- Consistent design across Portfolio, Watchlist, Alerts, and Analytics pages.
- Each shows a relevant Lucide icon (50% opacity), a friendly title, and an actionable hint.
- RTL-compatible, responsive.

**i18n:**
- 15+ new EN/FA translation keys for rule types, placeholders, empty states, and toast messages.

**Key files:**

```
backend/app/services/alerts.py          # _check_condition(), _notification_message(), updated evaluate_alerts()
backend/app/services/background.py      # Passes change_24h data to evaluate_alerts
backend/app/schemas/alert.py            # Extended direction validation, model_validator for target_price
frontend/src/components/ui/sonner.tsx    # Toaster component (sonner + project theme hook)
frontend/src/app/alerts/page.tsx         # Rule type selector, card layout on mobile, table on desktop
frontend/src/lib/alerts.ts              # AlertDirection type, updated createAlert()
frontend/src/lib/i18n/translations.ts   # New translation keys (EN + FA)
```

---

> **MVP Roadmap Complete.** Phases 1–7 represent the initial MVP roadmap. This repository state marks the end of the initial roadmap.

---

## Stage 3 — Product Hardening & Professionalization

The project has successfully completed the MVP stage (Phases 1–7) and is now entering a new phase focused on transforming the prototype into a professional-grade product.

This stage focuses on:

- **Product polish** — refining UX, improving interaction quality, and resolving rough edges across all pages.
- **Infrastructure stabilization** — hardening the backend, improving reliability, and preparing for production deployment.
- **External data integrations** — connecting real financial market data providers to replace mock data.
- **Branding and media assets** — establishing platform identity with logos, banners, and educational media.
- **Reliability and scalability improvements** — addressing caching, database migrations, error handling, and monitoring.
- **Improving the user experience across devices** — ensuring consistent, polished behavior on mobile, tablet, and desktop.

### Development Tracks

Stage 3 work is organized across parallel tracks rather than linear phases. Multiple tracks can progress simultaneously, and each track groups related work for clarity and focus.

| Track | Focus |
|---|---|
| **Product Experience Track** | UI polish, usability improvements, responsiveness, interaction quality. |
| **Live Market Data Track** | Integration of external financial market data providers. |
| **Branding & Media Track** | Platform assets, branding elements, educational media, banners. |
| **Design System Track** | UI consistency, reusable components, visual hierarchy, spacing and typography systems. |
| **Reliability & Infrastructure Track** | System stability, performance improvements, backend robustness. |

### Market Data Integration Strategy

Market data integrations follow a backend-driven approach:

- **Market providers are integrated via the backend.** The frontend should not directly call external data providers.
- **Data normalization is handled in backend services.** External API responses are transformed into a consistent internal format before being served to the frontend.
- **Provider abstraction layers should be used where possible.** Each external provider should be wrapped behind an adapter interface, making it straightforward to swap or add providers without changing downstream code.
- **Rate limit awareness and caching** are required for all external provider integrations to avoid service disruptions and unnecessary API costs.

### Stage 3 — Implementation Progress

The market data system has been implemented through several focused phases, each delivered as a separate PR and merged to `main`.

#### Phase A — Provider Abstraction Layer (PR #20)

Established a vendor-independent architecture for market data integration:

- Created `backend/app/providers/` package with Protocol-based provider abstraction
- Defined normalized market data types (`NormalizedQuote`, `NormalizedPriceHistory`, `NormalizedEconomicSeries`) as the internal data contract between providers and services
- Built CoinGecko provider adapter — isolated all CoinGecko-specific JSON parsing and HTTP calls inside the adapter
- Implemented in-memory caching layer with per-key TTL and stale-while-revalidate support
- Created mock provider for development and fallback scenarios
- Refactored `market_data_service.py` to use the provider abstraction instead of direct CoinGecko calls

This phase established the foundation for adding new providers without modifying the service or API layers.

#### Phase B — Multi-Provider System (PR #21)

Validated the provider abstraction by integrating a second real data provider:

- Added Finnhub provider adapter for US equity quotes (AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA)
- Created provider registry (`providers/registry.py`) for symbol-to-provider routing: crypto → CoinGecko, stocks → Finnhub, unknown → Mock
- Refactored service layer to route through the registry, making it fully provider-agnostic
- Added `source` field to all quote responses for provider attribution transparency
- Enforced the no-silent-mock guarantee: symbols with real providers never silently fall back to mock data on failure (stale cache or 503 instead)
- Expanded test coverage with 34 new provider tests

#### Phase C — Reliability & Observability (PR #22)

Improved production readiness with structured logging and error classification:

- Added structured logging to all provider HTTP calls: provider name, endpoint, latency (ms), success/failure status
- Classified provider errors into four types: `rate_limit` (HTTP 429), `timeout`, `http_error`, `parse_error`
- Explicit rate-limit detection — HTTP 429 responses logged with `status=rate_limit` for easy filtering
- Consistent exception handling across all providers — `get_quotes()` and `get_price_history()` always return safe defaults on failure
- Added 11 new resilience tests verifying error logging, rate-limit detection, and failure safety

These improvements enable production debugging and provider monitoring without adding infrastructure complexity.

#### Phase D — Portfolio Analytics Engine (PR #24)

Introduced a dedicated analytics layer that computes portfolio performance metrics using the market data provider system:

- Created `app/services/analytics/` package with clear separation of concerns: `metrics.py` (pure calculations), `allocation.py` (weights and diversification), `portfolio_analytics.py` (orchestrator)
- Analytics layer depends only on `market_data_service` — never imports provider modules directly
- Normalizes DB transactions into `PortfolioPosition` dataclass inside the analytics layer (no DB schema changes)
- Single `market_data_service` call per analytics request
- New endpoint: `GET /api/portfolio/analytics` returning total value, cost basis, PnL, return %, allocation weights, and diversification metrics
- Handles edge cases gracefully: empty portfolios return zeros, missing prices excluded from value calculations
- 38 unit tests covering metrics, allocation, normalization, orchestration, and edge cases

#### Phase E — Portfolio Snapshot & History API (PR #25)

Introduced portfolio history tracking through a lightweight snapshot system that records portfolio value over time:

- Created `PortfolioSnapshot` model storing computed metrics (total value, cost, PnL, asset count) per timestamp
- Snapshot creation service reuses the existing analytics engine — does not recompute metrics or call providers directly
- Introduced `repositories/` layer for clean data access separation
- New endpoints: `POST /api/portfolio/snapshot` (manual snapshot creation), `GET /api/portfolio/history` (timeseries read with range filtering: 7d, 30d, 90d, 1y)
- Snapshots store computed portfolio metrics, not raw transactions
- 16 unit tests covering repository operations, service orchestration, API endpoints, range filtering, user isolation, and edge cases

> **Detailed architecture documentation:** See [`MARKET_DATA_ARCHITECTURE_PROPOSAL.md`](MARKET_DATA_ARCHITECTURE_PROPOSAL.md) for full design decisions, data contracts, caching strategy, error handling model, and implementation details.

---

### For AI agents

1. **Read `PROJECT_CONTEXT.md` first** before making any changes.
2. **Read `DEVIN_GUIDE.md`** for product direction, development standards, and architectural principles.
3. Read [`MARKET_DATA_ARCHITECTURE_PROPOSAL.md`](MARKET_DATA_ARCHITECTURE_PROPOSAL.md) for detailed market data architecture and provider system design.
4. Read `AI_DEVELOPMENT_GUIDE.md` if it exists.
5. Read `frontend/AGENTS.md` — Next.js 16 has breaking changes from common training data.
6. Always work on a feature branch; never commit to `main`.
7. GitHub is the single source of truth.

## Archived Branches (May 2026)

The following branches contained incomplete experimental work and should not be continued:
- archive/notifications-system-mvp
- archive/price-alerts-module

Phase 7 was implemented on:
- feature/alerts-polish (merged via PR #18)

---

## 7. Roadmap / Next Steps

| Priority | Feature | Status | Description |
|---|---|---|---|
| 1 | Portfolio Module | Done | Record transactions, view positions, P&L, and allocation chart. |
| 2 | Watchlist | Done | Track favourite symbols with live prices. Add/remove symbols, duplicate prevention, user isolation. |
| 3 | Real Market Data Providers | In Progress | Provider abstraction layer with CoinGecko (crypto) and Finnhub (US stocks). Registry-based routing, structured logging, observability. Portfolio analytics engine. See [architecture docs](MARKET_DATA_ARCHITECTURE_PROPOSAL.md). |
| 4 | Economic Calendar | Planned | Surface upcoming earnings, FOMC meetings, and macro data releases. |
| 5 | Price Alerts | Done | Simple one-time trigger alerts with background worker (60s). Triggered state visible in UI. |
| 5b | Notifications (MVP) | Done | In-app notifications triggered by price alerts. Read/unread state, navbar badge, dedicated page. |
| 5c | Portfolio Analytics (MVP) | Done | Performance dashboard with overview cards, allocation pie charts, historical line chart, top movers. 5-min in-memory caching. |
| 6 | CI/CD Pipeline | Done | GitHub Actions CI with parallel backend (ruff + pytest) and frontend (ESLint + build) jobs. |
| 7 | AI Analysis Tools | Planned | Summarise trends, generate trade ideas, or score sentiment with LLMs. |
| 8a | UI Phase 1 — Theme System | Done | Dark/light theme with CSS tokens, toggle, localStorage persistence, anti-FOUC. |
| 8b | UI Phase 2 — Typography | Done | Inter + Vazirmatn fonts, typography tokens, heading/body styles. |
| 8c | UI Phase 3 — Responsive Layouts | Done | Mobile-first grids, hamburger menu, edge-to-edge tables. |
| 8d | UI Phase 4 — i18n + RTL | Done | EN/FA translations, locale toggle, dynamic RTL, Tailwind directional variants. |
| 8e | UI Phase 5 — Smart Summary Card | Done | Market insights card: avg change, best/worst performers, responsive layout. |
| 8f | UI Phase 6 — Benchmark Comparison | Done | Benchmark selector (None/BTC/S&P 500) on analytics chart, dashed amber line, normalized to portfolio scale, mock data via seeded PRNG. |
| 8g | UI Phase 7 — Alerts Upgrade + UX Polish | Done | Four alert rule types (price_above/below, daily_change_above/below), toast notifications (sonner), skeleton loaders (Dashboard/Portfolio/Analytics), empty states, mobile card layout for alerts. |
