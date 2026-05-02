# PROJECT_CONTEXT.md

> A quick-reference guide for developers and AI agents working on this repository.

---

## 1. Overview

**AI Finance WebApp** is a modular financial web application that provides a dashboard for viewing market data, managing authentication, and (in the future) tracking portfolios.

- **Typical user:** A retail investor or finance enthusiast who wants a single dashboard to monitor prices, manage a watchlist, and analyse market trends.
- **Current maturity:** Early MVP. The app has JWT-based authentication, mock market data for three symbols, and a portfolio module for recording transactions and tracking positions. There is no real brokerage integration or production database yet.

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
| HTTP client | httpx 0.28 (available for future external API calls) |

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

### 4.2 Market Data Module (Mock)

**Supported symbols:** BTC (Bitcoin, base $62,450), ETH (Ethereum, base $3,180), AAPL (Apple Inc., base $189.50). Prices are generated with deterministic random jitter (`seed=42`).

**Backend endpoints** (prefix: `/api/market-data`):

| Method | Route | Description | Auth required |
|---|---|---|---|
| GET | `/api/market-data/latest` | Returns current mock quotes for all symbols (price, change, change %). | No |
| GET | `/api/market-data/history?symbol=BTC&days=30` | Returns daily mock price points for a symbol. Returns 404 for unknown symbols. `days` defaults to 30 (max 365). | No |

**Frontend components:**
- `<MarketDataSection>` — orchestrates price cards and chart.
- `<PriceCard>` — shows symbol name, price, daily change with green/red colour coding. Clicking a card selects the symbol.
- `<PriceChart>` — 30-day line chart rendered with Recharts for the selected symbol.

**Key files:**

```
backend/app/api/v1/endpoints/market_data.py   # Route handlers
backend/app/services/market_data.py            # Mock data generation
backend/app/schemas/market_data.py             # Pydantic models (MarketQuote, PricePoint)

frontend/src/components/shared/market-data-section.tsx
frontend/src/components/shared/price-card.tsx
frontend/src/components/shared/price-chart.tsx
frontend/src/lib/market-data.ts                # API client for market data
```

**Future extension:**
- Replace `backend/app/services/market_data.py` with real API calls (e.g. CoinGecko, Alpha Vantage, Yahoo Finance). The service functions have the same interface so the routes do not need to change.
- Add WebSocket support for real-time price streaming.
- Protect market data endpoints with `Depends(get_current_user)` if desired.

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
- Current price fetched from the Market Data mock service.
- Unrealized P&L = (current_price − avg_buy_price) × quantity.

**Validation rules:**
- Cannot sell more than the currently owned quantity.
- Quantity and price must be > 0.
- All endpoints require JWT authentication.

**Frontend pages:**
- `/portfolio` — Protected page showing summary cards (Total Value, Total Invested, P&L, Return %), positions table, portfolio allocation chart (Recharts), and transaction history table.
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
│       │           └── portfolio.py  # POST/GET transactions, GET summary
│       ├── core/
│       │   ├── config.py            # Settings (pydantic-settings)
│       │   ├── database.py          # SQLAlchemy engine, session, Base
│       │   ├── deps.py              # get_current_user dependency
│       │   └── security.py          # JWT + password hashing utilities
│       ├── models/
│       │   ├── user.py              # User ORM model
│       │   └── portfolio.py         # PortfolioTransaction ORM model
│       ├── schemas/
│       │   ├── auth.py              # UserRegister, UserLogin, UserResponse, TokenResponse
│       │   ├── market_data.py       # MarketQuote, PricePoint, response wrappers
│       │   └── portfolio.py         # TransactionCreate, PositionResponse, PortfolioSummaryResponse
│       └── services/
│           ├── auth.py              # create_user, authenticate_user, get_user_by_email
│           ├── market_data.py       # Mock quote and history generators
│           └── portfolio.py         # Position calculation, validation, P&L
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
        │   └── portfolio/
        │       ├── page.tsx          # Portfolio dashboard (positions, summary, chart)
        │       └── new-transaction/
        │           └── page.tsx      # New transaction form
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
| 2 | Watchlist | Planned | Save favourite symbols and receive summary updates. |
| 3 | Real Market Data Providers | Planned | Integrate CoinGecko, Alpha Vantage, or Yahoo Finance to replace mock data. |
| 4 | Economic Calendar | Planned | Surface upcoming earnings, FOMC meetings, and macro data releases. |
| 5 | Alerts System | Planned | Notify users (email / push) when a price crosses a threshold. |
| 6 | AI Analysis Tools | Planned | Summarise trends, generate trade ideas, or score sentiment with LLMs. |
