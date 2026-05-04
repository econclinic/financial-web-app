# AI Finance WebApp

A professional, modular financial web application built with **FastAPI** (backend) and **Next.js** (frontend).

## Project Structure

```
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/v1/           # Versioned API routes
│   │   ├── core/             # Configuration & security
│   │   ├── models/           # SQLAlchemy / PostgreSQL models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # Business logic (market data, etc.)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Next.js (App Router) frontend
│   ├── src/
│   │   ├── app/              # Pages & layouts
│   │   ├── components/       # UI, shared, and layout components
│   │   ├── hooks/            # Custom React hooks
│   │   └── lib/              # Utilities & API clients
│   └── Dockerfile
├── docker-compose.yml        # Orchestration (backend + frontend + PostgreSQL)
└── .env.example              # Environment variable template
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.12+ (for local backend development)

### Quick Start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/openapi.json
- **Health Check**: http://localhost:8000/api/v1/health

### Local Development

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Tech Stack

| Layer      | Technology                             |
| ---------- | -------------------------------------- |
| Frontend   | Next.js 16, React 19, Tailwind CSS v4  |
| UI Library | Shadcn UI, Lucide React                |
| Backend    | FastAPI, SQLAlchemy, Pydantic          |
| Database   | SQLite (MVP) / PostgreSQL 16 (prod)    |
| Infra      | Docker Compose                         |

## Features

- **Authentication** — JWT-based register/login with protected routes
- **Market Data** — Real-time crypto prices (CoinGecko) with 60s caching, mock stocks
- **Portfolio** — Record buy/sell transactions, track positions with live P&L
- **Watchlist** — Track favourite symbols with live prices and 24h change
- **Price Alerts** — Set above/below price thresholds; background worker checks every 60s and triggers once when condition is met
- **CI/CD** — GitHub Actions with parallel backend (ruff + pytest) and frontend (ESLint + build) jobs

See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for detailed architecture and module documentation.
