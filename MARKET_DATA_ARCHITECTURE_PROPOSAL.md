# Market Data Architecture Proposal — Stage 3

> Technical architecture design for integrating external market data providers.
> This is the authoritative detailed architecture document for the market data system.
>
> For high-level project context and overall progress, see [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md).

---

## 1. High-Level Architecture

### Current State

```
Frontend (Next.js)
    │
    │  GET /api/market-data/latest
    │  GET /api/market-data/history
    │  GET /api/market/prices
    ▼
FastAPI API Layer
    │
    ├── market_data.py ──► get_latest_quotes()
    │                        ├── get_live_prices() ──► CoinGecko (BTC, ETH)
    │                        └── mock jitter (AAPL)
    │
    └── market.py ──────► get_live_prices() ──► CoinGecko
                           └── 60s in-memory cache (dict)
```

**Problems with current architecture:**
- CoinGecko is called directly from `market_data_service.py` — no abstraction layer.
- AAPL uses mock data hardcoded in `market_data.py`.
- No provider interface — adding Finnhub or FRED means writing parallel logic.
- Cache is a module-level dict — lost on restart, no TTL per key, no stale-while-revalidate.
- No error categorization (rate limit vs timeout vs provider down).

### Proposed Architecture

```
Frontend (Next.js)
    │
    │  Normalized internal API contracts
    │  (MarketQuote, PriceHistory, EconomicSeries, NewsArticle)
    ▼
┌─────────────────────────────────────────────────┐
│              FastAPI API Layer                   │
│   /api/market-data/*   /api/macro/*   /api/news/*│
│                                                 │
│   Response schemas: Pydantic models             │
│   (provider-independent, stable contracts)      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│           Market Data Service Layer             │
│                                                 │
│   Orchestrates providers, handles fallback,     │
│   merges multi-provider data, returns           │
│   normalized internal schemas.                  │
│                                                 │
│   market_service.py                             │
│   macro_service.py                              │
│   news_service.py                               │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              Caching Layer                       │
│                                                 │
│   In-memory (MVP) → Redis (production)          │
│   Per-key TTL, stale-while-revalidate,          │
│   request coalescing                            │
│                                                 │
│   cache.py                                      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│           Provider Adapter Layer                 │
│                                                 │
│   Each provider implements a common Protocol.    │
│   Adapters normalize external responses into     │
│   internal data classes.                         │
│                                                 │
│   providers/                                     │
│   ├── base.py          # Protocol definitions    │
│   ├── coingecko.py     # CoinGecko adapter       │
│   ├── finnhub.py       # Finnhub adapter         │
│   ├── fred.py          # FRED adapter            │
│   ├── mock.py          # Mock/fallback adapter   │
│   └── marketaux.py     # News adapter (future)   │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
          External Provider APIs
   (CoinGecko, Finnhub, FRED, etc.)
```

### Proposed Directory Structure

```
backend/app/
├── providers/                    # Provider adapter layer
│   ├── __init__.py
│   ├── base.py                   # Protocol/ABC definitions
│   ├── types.py                  # Internal data classes (normalized)
│   ├── cache.py                  # Caching utilities
│   ├── registry.py               # Symbol → provider routing
│   ├── coingecko.py              # CoinGecko adapter (crypto)
│   ├── finnhub.py                # Finnhub adapter (US stocks)
│   ├── fred.py                   # FRED adapter (future)
│   ├── mock.py                   # Mock data adapter (dev/fallback)
│   └── marketaux.py              # News adapter (future)
├── services/
│   ├── market_service.py         # REFACTORED — orchestrates providers
│   ├── macro_service.py          # NEW — macroeconomic data service
│   ├── news_service.py           # NEW — news aggregation service (future)
│   ├── market_data_service.py    # DEPRECATED → migrated to providers/coingecko.py
│   ├── market_data.py            # DEPRECATED → migrated to market_service.py
│   └── ...                       # existing services unchanged
├── schemas/
│   ├── market_data.py            # STABLE — existing schemas preserved
│   ├── macro.py                  # NEW — macroeconomic response schemas
│   └── ...
└── api/v1/endpoints/
    ├── market_data.py            # Existing endpoints — contract preserved
    ├── market.py                 # Existing endpoint — contract preserved
    ├── macro.py                  # NEW — macroeconomic data endpoints
    └── ...
```

### Key Design Principles

1. **The `providers/` directory owns all external communication.** No other module should import `httpx` or call external URLs directly.
2. **The service layer orchestrates providers** — selects which provider to use, handles fallback, merges results.
3. **The API layer returns stable Pydantic schemas** — the frontend sees the same response structure regardless of which provider is active.
4. **Existing API contracts are preserved.** Current frontend code continues working without changes.

### Service Layer Responsibility Boundaries

> **Architectural guardrail — applies to all Stage 3 and future work.**

The service layer and provider adapters have clearly separated responsibilities:

| Layer | Responsibility | Must NOT do |
|---|---|---|
| **Service layer** (`services/`) | Orchestrate provider selection, handle fallback logic, merge multi-provider results, enforce caching policy, return normalized types to API layer. | Parse raw provider payloads. Transform external data formats. Import provider-specific libraries. |
| **Provider adapters** (`providers/`) | Call external APIs, parse raw responses, normalize external data into internal `types.py` data classes, handle provider-specific error codes, manage rate limits. | Make business logic decisions. Access the database. Decide fallback routing. |
| **API layer** (`api/`) | Accept HTTP requests, validate input, call service layer, return Pydantic response models. | Call providers directly. Parse external data. Implement caching. |

**Key rule: Services must never parse raw provider payloads directly.** All provider-specific transformation logic — JSON parsing, field mapping, unit conversion, error code interpretation — is isolated inside the adapter that owns that provider. The service layer only works with normalized internal types (`NormalizedQuote`, `NormalizedPriceHistory`, etc.).

This ensures that adding or replacing a provider never requires changes to the service layer or API layer — only a new adapter file in `providers/`.

---

## 2. Provider Strategy

### Classification

| Category | Provider | Stage | Role | Notes |
|---|---|---|---|---|
| Crypto | **CoinGecko** | Development + Production | Primary | Already integrated. Reliable. Upgrade tier when needed. |
| Crypto | **Mock** | Development | Fallback | Existing mock data for offline/testing. |
| US Stocks | **Finnhub** | Development + Production | Primary | Free tier (60/min). First real stock data integration. |
| US Stocks | **Mock** | Development | Fallback | Existing AAPL mock data. Keep as offline fallback. |
| International Stocks | **Twelve Data** | Future Production | Primary | Add when international coverage is needed. Requires paid plan. |
| Macroeconomic | **FRED** | Development + Production | Primary | Completely free. Government-backed. |
| News | **Finnhub** | Development | Primary | Company news included in free tier. |
| News | **Marketaux** | Future Production | Enhanced | Add for sentiment analysis features. |
| Iran/TSE | **TSETMC** | Experimental | Optional | Unofficial scraper. Beta quality. Dedicated adapter with aggressive caching. |

### Provider Selection Logic

```
For each data request:
1. Try PRIMARY provider
2. If primary fails → return CACHED data (stale-while-revalidate)
3. If no cache → try FALLBACK provider (mock)
4. If no fallback → return error response with clear message
```

The service layer decides which provider is "primary" based on configuration. This allows:
- Development: mock provider for offline work
- Staging: real providers with relaxed caching
- Production: real providers with aggressive caching

Provider selection should be configurable via environment variables:

```
MARKET_PROVIDER_CRYPTO=coingecko      # or "mock"
MARKET_PROVIDER_STOCKS=finnhub        # or "mock"
MARKET_PROVIDER_MACRO=fred            # or "mock"
MARKET_PROVIDER_NEWS=finnhub          # or "none"
```

---

## 3. Internal API Contract Philosophy

### Core Principle

**The frontend consumes normalized, provider-independent schemas. It never knows or cares which provider sourced the data.**

### Normalized Internal Data Types

These are the canonical internal representations that all providers must produce. They live in `providers/types.py` as plain dataclasses (not Pydantic — those are for API responses):

#### Quote Data

```python
@dataclass
class NormalizedQuote:
    symbol: str              # Internal symbol (e.g., "BTC", "AAPL")
    name: str                # Human-readable name
    price: float             # Current price in USD
    change_24h: float        # Absolute price change (24h)
    change_24h_pct: float    # Percentage change (24h)
    volume_24h: float | None # 24h trading volume (optional)
    market_cap: float | None # Market cap (optional)
    source: str              # Provider name (for logging/debugging)
    timestamp: datetime      # When this data was fetched
```

#### Price History

```python
@dataclass
class NormalizedPricePoint:
    timestamp: datetime
    open: float | None       # OHLC — None if not available
    high: float | None
    low: float | None
    close: float             # Close price (required)
    volume: float | None

@dataclass
class NormalizedPriceHistory:
    symbol: str
    name: str
    interval: str            # "1d", "1h", "5m", etc.
    points: list[NormalizedPricePoint]
    source: str
```

#### Economic Data

```python
@dataclass
class NormalizedEconomicSeries:
    series_id: str           # e.g., "GDP", "CPI", "UNRATE"
    name: str                # Human-readable name
    unit: str                # e.g., "Billions of Dollars", "Percent"
    frequency: str           # "monthly", "quarterly", "annual"
    observations: list[NormalizedObservation]
    source: str

@dataclass
class NormalizedObservation:
    date: date
    value: float | None      # None for missing observations
```

#### News

```python
@dataclass
class NormalizedNewsArticle:
    title: str
    summary: str
    url: str
    source_name: str         # Publication name
    published_at: datetime
    symbols: list[str]       # Related ticker symbols
    sentiment: float | None  # -1.0 to 1.0 (None if unavailable)
    image_url: str | None
```

### API Response Schemas (Pydantic)

The existing `MarketQuote`, `PricePoint`, `MarketDataLatestResponse`, and `MarketDataHistoryResponse` schemas remain stable. New endpoints use new schemas:

```python
# schemas/macro.py (new)
class EconomicSeriesResponse(BaseModel):
    series_id: str
    name: str
    unit: str
    frequency: str
    observations: list[ObservationPoint]

class ObservationPoint(BaseModel):
    date: str               # ISO date
    value: float | None
```

### Contract Stability Rules

1. **Existing response schemas are never modified in breaking ways.** New fields can be added (backward-compatible). Existing fields are never removed or renamed.
2. **New data categories get new endpoints and schemas.** Macroeconomic data does not get shoehorned into market data endpoints.
3. **The `source` field is internal-only.** It appears in logs and debug responses, never in production API responses to the frontend.

---

## 4. Caching Strategy

### Cache Architecture

```
Request → Service Layer → Cache Check
                            │
                    ┌───────┴────────┐
                    │  Cache HIT     │  Cache MISS / STALE
                    │  (fresh)       │
                    │                │
                    ▼                ▼
               Return cached    Fetch from provider
                                    │
                              ┌─────┴─────┐
                              │ Success    │ Failure
                              │            │
                              ▼            ▼
                         Update cache   Return stale cache
                         Return fresh   (or error if no cache)
```

### Cache TTL Recommendations

| Data Type | TTL | Rationale |
|---|---|---|
| Live crypto quotes | 60 seconds | Balance freshness vs CoinGecko rate limits. Current value works well. |
| Live stock quotes | 60 seconds | Same rationale. Finnhub free tier supports this at 60 calls/min. |
| 24h change data | 60 seconds | Bundled with quote requests. |
| Price history (daily) | 15 minutes | Historical data changes slowly (once per day for daily bars). |
| Price history (intraday) | 60 seconds | More volatile, needs fresher data. |
| Economic indicators (FRED) | 1 hour | Macro data updates infrequently (monthly/quarterly releases). |
| Company news | 5 minutes | News is time-sensitive but not second-level critical. |
| Symbol metadata (name, type) | 24 hours | Rarely changes. |

### Request Coalescing

When multiple users request the same symbol simultaneously, only one external API call should be made:

```python
# Concept — not implementation code
class CoalescingCache:
    """If a fetch for key K is already in-flight, subsequent
    requests for K await the same result instead of making
    duplicate external calls."""

    _in_flight: dict[str, asyncio.Future]

    async def get_or_fetch(self, key, fetch_fn):
        if key in self._in_flight:
            return await self._in_flight[key]   # wait for existing request
        future = asyncio.ensure_future(fetch_fn())
        self._in_flight[key] = future
        try:
            result = await future
            self._store(key, result)
            return result
        finally:
            del self._in_flight[key]
```

This prevents the "thundering herd" problem where 100 users loading the dashboard triggers 100 CoinGecko calls.

### Stale-While-Revalidate

When cached data has expired:
1. Return the **stale cached value** immediately (fast response).
2. Trigger a **background refresh** to update the cache.
3. Next request gets the fresh value.

This prevents users from waiting on slow provider responses. The trade-off is data may be up to 2x TTL old in the worst case — acceptable for 60-second TTLs.

### Rate-Limit Protection

```python
class RateLimiter:
    """Tracks API call count per provider per time window.
    Rejects requests that would exceed the provider's rate limit."""

    def __init__(self, max_calls: int, window_seconds: int):
        ...

    def allow(self) -> bool:
        """Returns True if a call is allowed, False if rate limit reached."""
        ...
```

Each provider adapter includes a rate limiter configured to the provider's documented limits:

| Provider | Rate Limit Config |
|---|---|
| CoinGecko (demo) | 30 calls/min |
| Finnhub (free) | 60 calls/min |
| FRED | 120 calls/min (2/sec) |
| Twelve Data (free) | 8 calls/min |

When the rate limiter returns `False`, the service falls back to cached data rather than making the call.

### MVP vs Production Cache

| Phase | Implementation |
|---|---|
| **MVP (Stage 3 initial)** | In-memory dict with TTL tracking (evolution of current pattern). Simple, no new dependencies. |
| **Production (later)** | Redis with TTL. Survives restarts. Shared across worker processes. Add when scaling requires it. |

The `cache.py` module should abstract the storage backend so the switch from dict to Redis is a single-line config change.

### Multi-Worker Cache Limitation

> **Operational note for Stage 3.**

The Stage 3 in-memory cache assumes a **single-process backend deployment** (single Uvicorn worker). Each worker process maintains its own independent cache — there is no cache sharing between processes.

Redis (or an equivalent shared cache) becomes **required** before any of the following:

- **Multi-worker Uvicorn/Gunicorn setups** (`--workers N` where N > 1) — each worker would maintain its own cache, multiplying external API calls by the worker count and serving inconsistent data across requests.
- **Horizontal scaling** — multiple backend instances behind a load balancer have no shared state.
- **Multiple backend containers** — Docker Compose or Kubernetes deployments with replicated backend services.

Until Redis is introduced, the backend should be deployed as a single-worker process. This is acceptable for Stage 3 scale. The `cache.py` abstraction is designed so that swapping the in-memory backend for Redis requires changing only the cache backend configuration, not the service or adapter code.

---

## 5. Error Handling Strategy

### Error Categories

| Category | Examples | Response Strategy |
|---|---|---|
| **Provider timeout** | Network timeout, DNS failure, connection refused | Return cached data. Log warning. Retry on next request cycle. |
| **Rate limit exceeded** | HTTP 429, rate limiter pre-check | Return cached data. Log info. Back off automatically. |
| **Provider error** | HTTP 500, malformed response, schema mismatch | Return cached data. Log error with response details. |
| **Data not available** | Symbol not found, endpoint not supported | Return clear error to frontend (404 or empty). |
| **No cache, no provider** | First request ever + provider is down | Return HTTP 503 with descriptive message. |

### Error Response Contract

Provider failures should never leak raw external error details to the frontend. The API layer returns:

```python
# Success with degraded data
{
    "data": [...],           # whatever is available
    "meta": {
        "stale": true,       # indicates data may be outdated
        "last_updated": "2026-05-12T18:00:00Z"
    }
}

# Complete failure
HTTP 503
{
    "detail": "Market data temporarily unavailable. Please try again later."
}
```

### Provider Health Tracking

Each provider adapter tracks its recent success/failure rate:

```
- Last N request outcomes (ring buffer)
- Current status: healthy / degraded / down
- Time of last successful response
```

The service layer uses this to make provider selection decisions:
- If primary is "down" and fallback exists → use fallback immediately (don't wait for timeout).
- If primary is "degraded" → try primary with shorter timeout, fall back quickly.

### Circuit Breaker Pattern (Future Hardening)

> **Note:** The full circuit breaker pattern is documented here for architectural completeness but is **not part of the Stage 3 initial implementation scope.**

```
CLOSED (normal) ──[N consecutive failures]──► OPEN (skip provider)
                                                │
                                         [wait cooldown period]
                                                │
                                                ▼
                                         HALF-OPEN (try one request)
                                                │
                                    ┌───────────┴──────────┐
                                    │ Success              │ Failure
                                    ▼                      ▼
                                 CLOSED                  OPEN
```

This prevents wasting rate limit quota on a provider that's clearly down, and avoids making users wait for timeouts on every request.

**Recommended thresholds (when implemented):**
- Open after 5 consecutive failures
- Cooldown: 60 seconds
- Half-open: allow 1 test request

### Stage 3 Error Resilience Scope

For the initial Stage 3 implementation, the error handling scope is:

| Mechanism | Stage 3 Scope | Description |
|---|---|---|
| **Timeout handling** | Yes | All provider HTTP calls use explicit timeouts (10s default). Timeout triggers fallback to cache. |
| **Stale cache fallback** | Yes | On any provider failure, return the last cached value if available. Only return an error if no cached data exists. |
| **Retry with backoff** | Yes | On transient failures (timeout, 5xx), retry once with a short delay (1–2s) before falling back to cache. Do not retry on 4xx or rate limit (429) responses. |
| **Circuit breaker** | Future | Full state machine (closed/open/half-open) is deferred to a future hardening phase. |

This provides robust error handling for the common failure modes (provider timeouts, transient outages, rate limits) without the complexity of a full circuit breaker state machine.

---

## 6. Scalability Considerations

### Future WebSocket Support

The current architecture polls providers via REST. Future WebSocket support should be designed as a **separate concern** that feeds into the same caching layer:

```
WebSocket Connection (persistent)
    │
    │  Real-time price updates
    ▼
Cache Layer (write)
    │
    │  Updated prices available immediately
    ▼
REST API (read from cache)
    │
    │  Responses always fresh
    ▼
Frontend
```

**Implementation approach:**
1. A background asyncio task maintains WebSocket connections to providers (Finnhub, CoinGecko Analyst+).
2. Incoming messages update the cache directly.
3. REST endpoints read from cache — no change to API contracts.
4. Later: expose a WebSocket endpoint from the backend to the frontend for real-time push (optional, not required for Stage 3).

**This means WebSocket support doesn't change the frontend at all** — it just makes cached data fresher. The frontend can opt into WebSocket later for real-time updates.

### Multi-Provider Aggregation

For high-reliability production scenarios, the service layer could query multiple providers and merge results:

```
Request for BTC quote
    │
    ├── CoinGecko → $67,500
    ├── Finnhub   → $67,480
    │
    ▼
Aggregation logic:
    - Use primary provider's price
    - Cross-validate: if prices diverge > 1%, log warning
    - If primary fails, seamlessly use secondary
```

This is **not needed for Stage 3** but the adapter pattern makes it straightforward to add later.

### Background Jobs

The existing background worker pattern (60s alert evaluation loop) should be extended:

| Job | Interval | Purpose |
|---|---|---|
| Alert evaluation | 60 seconds | Existing — check alerts against current prices. |
| Cache warming | 60 seconds | Pre-fetch popular symbols so first user request is always cached. |
| Provider health check | 5 minutes | Ping each provider, update health status, log availability. |
| Rate limit reset | Per provider window | Reset rate limit counters. |

All jobs run in the existing `background.py` asyncio task loop — no new infrastructure needed.

### Queue/Event Possibilities (Future)

For later scaling beyond a single process:

| Pattern | Use Case | When to Add |
|---|---|---|
| **Task queue (Celery/ARQ)** | Heavy analytics computations, batch data fetching | When analytics take >5 seconds or multiple workers are needed. |
| **Event bus (Redis pub/sub)** | Real-time price updates across worker processes | When running multiple backend instances behind a load balancer. |
| **Message queue (RabbitMQ)** | Reliable alert delivery, notification channels | When adding email/push notification channels. |

**None of these are needed for Stage 3.** The single-process asyncio model is sufficient for the current scale. Document the upgrade path but don't build it yet.

### Analytics Pipeline (Future)

```
Provider Data → Cache → Analytics Service → Pre-computed Results → API
```

Currently, analytics are computed on-demand with 5-minute caching. As data volume grows:
1. Move analytics computation to background jobs (compute every N minutes).
2. Store pre-computed results in the database.
3. API endpoints serve pre-computed data (fast reads).

This is a **future optimization** — the current on-demand pattern works fine at MVP scale.

---

## 7. Security and Operational Concerns

### API Key Management

| Provider | Key Required | Storage |
|---|---|---|
| CoinGecko (demo) | Yes (free registration) | Environment variable: `COINGECKO_API_KEY` |
| CoinGecko (paid) | Yes | Environment variable: `COINGECKO_API_KEY` |
| Finnhub | Yes (free registration) | Environment variable: `FINNHUB_API_KEY` |
| FRED | Yes (free registration) | Environment variable: `FRED_API_KEY` |
| Twelve Data | Yes (free registration) | Environment variable: `TWELVEDATA_API_KEY` |
| Marketaux | Yes (free registration) | Environment variable: `MARKETAUX_API_KEY` |

### Environment Variable Configuration

Add to `backend/app/core/config.py`:

```python
# Market data provider keys
COINGECKO_API_KEY: str = ""          # Demo key (free registration)
FINNHUB_API_KEY: str = ""            # Free tier key
FRED_API_KEY: str = ""               # Free registration
TWELVEDATA_API_KEY: str = ""         # Free tier key
MARKETAUX_API_KEY: str = ""          # Free tier key

# Provider selection
MARKET_PROVIDER_CRYPTO: str = "coingecko"
MARKET_PROVIDER_STOCKS: str = "mock"     # "finnhub" when ready
MARKET_PROVIDER_MACRO: str = "mock"      # "fred" when ready
MARKET_PROVIDER_NEWS: str = "none"
```

### Security Rules

1. **API keys are never committed to the repository.** Use environment variables or `.env` file (already gitignored).
2. **API keys are never logged.** Mask keys in any debug/error output.
3. **API keys are never sent to the frontend.** All provider communication happens server-side only.
4. **Provider responses are never returned raw to the frontend.** Always normalize through internal schemas.
5. **Rate limit status is never exposed to the frontend.** Internal concern only.

### Monitoring and Logging

| What to Log | Level | Purpose |
|---|---|---|
| Provider API call (success) | DEBUG | Request/response audit trail |
| Provider API call (failure) | WARNING | Track reliability issues |
| Rate limit approached (>80% of quota) | WARNING | Early warning for upgrade decisions |
| Rate limit exceeded | ERROR | Immediate attention needed |
| Cache hit/miss ratio | INFO (periodic) | Optimize TTLs and caching strategy |
| Provider health status change | INFO | Track degradation events |
| Circuit breaker state change | WARNING | Provider is down/recovered |

Use Python's standard `logging` module (already available in the project). No new monitoring infrastructure needed for Stage 3.

### Observability Hooks

While no heavy monitoring stack is needed for Stage 3, the architecture should be **metrics-friendly** from the start. Lightweight observability hooks should be built into the provider and cache layers:

| Metric | Where to Track | How |
|---|---|---|
| **Provider latency** | Each adapter's `fetch` call | Log elapsed time per external API call. Track min/avg/max per provider via simple counters. |
| **Cache hit/miss rate** | `cache.py` get operations | Increment hit/miss counters per cache key prefix. Log ratios periodically (every 5 minutes). |
| **Provider failure count** | Each adapter's error handling | Count failures per provider per time window. Log when failure rate exceeds threshold (e.g., >20% in 5 minutes). |
| **Rate limit proximity** | Rate limiter (when implemented) | Log when a provider's call count exceeds 80% of its rate limit window. |

**Implementation approach for Stage 3:**
- Use module-level counters (simple `int` variables or `collections.Counter`) — no external dependencies.
- Log summary metrics via `logging.info()` on a periodic basis (e.g., every 5 minutes in the background worker).
- Design counter interfaces so they can later be replaced with Prometheus `Counter`/`Histogram` objects without changing call sites.

This ensures that when a proper observability stack is introduced (Prometheus, Grafana, etc.), the instrumentation points already exist and only the backend (counter implementation) needs to change.

**Future:** Add structured logging (JSON) and consider an observability stack (Prometheus metrics, Grafana dashboards) when the app reaches production scale.

---

## 8. Recommended Implementation Order

### Phase A — Foundation (Provider Adapter Layer) ✅

**Goal:** Establish the provider abstraction without changing any existing behavior.

1. Create `backend/app/providers/` directory with:
   - `base.py` — Protocol definitions (`MarketDataProvider`, `EconomicDataProvider`)
   - `types.py` — Normalized internal data classes
   - `cache.py` — Generic cache with TTL, stale-while-revalidate, coalescing
   - `mock.py` — Mock provider adapter (wraps existing mock logic)

2. Create `coingecko.py` adapter — wraps existing `market_data_service.py` logic behind the provider Protocol.

3. No API changes. No frontend changes. Existing tests pass.

**Risk:** Minimal. Internal refactor only.

### Phase B — Finnhub Integration (Stock Data) ✅

**Goal:** Replace AAPL mock data with real stock quotes.

1. Create `finnhub.py` adapter implementing `MarketDataProvider`.
2. Add `FINNHUB_API_KEY` to config.
3. Update `market_service.py` to route stock symbols through Finnhub, crypto through CoinGecko.
4. Update the mock provider as fallback when Finnhub is unavailable or key is not configured.
5. Add tests for Finnhub adapter (mock HTTP responses in tests).

**API contract:** Unchanged. `MarketQuote` schema already covers all fields. Frontend sees real AAPL prices where it previously saw mock data.

**Risk:** Low. Additive change. Fallback to mock preserves existing behavior.

### Phase C — Reliability & Observability ✅

**Goal:** Improve production readiness with structured logging and error classification.

1. Add structured logging to `_request()` in Finnhub and CoinGecko adapters (provider, endpoint, latency_ms, status).
2. Classify errors: `rate_limit` (429), `timeout`, `http_error`, `parse_error`.
3. Detect and log HTTP 429 rate-limit responses explicitly.
4. Ensure consistent exception handling across all providers.
5. Add resilience tests.

**API contract:** Unchanged. No behavior changes — purely observability improvements.

**Risk:** Minimal. Logging-only changes.

### Future — FRED Integration (Macroeconomic Data)

**Goal:** Add macroeconomic indicator data as a new feature.

1. Create `fred.py` adapter implementing `EconomicDataProvider`.
2. Create `macro_service.py` service layer.
3. Create `schemas/macro.py` with Pydantic response models.
4. Create `api/v1/endpoints/macro.py` with new endpoints:
   - `GET /api/macro/series/{series_id}` — fetch a specific economic series
   - `GET /api/macro/indicators` — list available indicators
5. Add `FRED_API_KEY` to config.
6. Add tests.

**API contract:** New endpoints only. No changes to existing endpoints. Frontend can consume when ready.

**Risk:** Low. Entirely new endpoints — no existing behavior affected.

### Phase D — Portfolio Analytics Engine ✅

**Goal:** Introduce a portfolio analytics layer that calculates performance metrics using normalized market data from `market_data_service`.

1. Create `app/services/analytics/` package with separated concerns:
   - `metrics.py` — Pure calculation functions (position value, portfolio value, cost basis, PnL, return %)
   - `allocation.py` — Allocation weights, largest position, asset count
   - `portfolio_analytics.py` — Orchestrator (retrieves positions, normalizes, fetches prices, assembles response)
2. Normalize DB transactions into `PortfolioPosition` dataclass inside the analytics layer (no DB schema changes).
3. Single `market_data_service.get_current_prices_map()` call per analytics request — no direct provider imports.
4. New endpoint: `GET /api/portfolio/analytics` returning total value, cost, PnL, return %, allocation, diversification.
5. Graceful handling of empty portfolios (zeros) and missing prices (excluded from value/allocation).
6. 38 unit tests covering metrics, allocation, normalization, orchestration, and edge cases.

**Dependency flow:** API → analytics layer → `market_data_service` → providers. Analytics never imports provider modules.

**API contract:** New endpoint only. No changes to existing endpoints.

**Risk:** Low. Entirely new module — no existing behavior affected.

### Phase E — Portfolio Snapshot & History API ✅

**Goal:** Introduce portfolio history tracking by recording portfolio value over time and exposing a history API for charting.

1. Created `PortfolioSnapshot` model (`id`, `user_id`, `timestamp`, `total_value`, `total_cost`, `total_pnl`, `asset_count`).
2. Snapshot creation service (`services/portfolio_snapshot_service.py`) reuses the existing analytics engine — does not recompute metrics or call providers directly.
3. Snapshot repository (`repositories/portfolio_snapshot_repository.py`) for clean data access with time-range queries and ordering.
4. New endpoints:
   - `POST /api/portfolio/snapshot` — Manual snapshot creation, returns the persisted snapshot.
   - `GET /api/portfolio/history?range=7d|30d|90d|1y` — Returns portfolio value timeseries from stored snapshots.
5. History API is a pure read layer — only returns stored snapshots, never recomputes analytics.
6. 16 unit tests covering repository, service, endpoints, range filtering, user isolation, and edge cases.

**Dependency flow:**

```
API
↓
Portfolio Snapshot / History API
↓
Portfolio Analytics Engine
↓
Market Data Service
↓
Providers
```

Snapshots consume analytics outputs only. No direct provider access. No analytics duplication.

**API contracts:** New endpoints only. No changes to existing endpoints.

**Not included:** Background workers, scheduled jobs, Redis, WebSocket, historical price reconstruction.

### Phase F — Portfolio Performance API ✅

**Goal:** Build a performance layer that uses stored portfolio snapshots to compute and expose return metrics. No market data calls, no analytics recomputation.

1. Performance service (`services/performance/portfolio_performance_service.py`) reads snapshots from the repository and computes return metrics.
2. Supports 7d, 30d, 90d, 1y return windows with absolute change and percentage return.
3. Uses closest-snapshot-at-or-before logic: if no snapshot exists at the exact cutoff, selects the most recent prior snapshot. Returns `null` if no suitable snapshot exists for a window.
4. Extended snapshot repository with `get_latest_snapshot` and `get_closest_snapshot_at_or_before` helpers.
5. New endpoints:
   - `GET /api/portfolio/performance` — Returns current value and return metrics for all windows.
   - `GET /api/portfolio/performance/history?range=7d|30d|90d|1y` — Returns snapshot timeseries with `total_value`, `total_cost`, `total_pnl`.
6. 20 unit tests covering service, repository, endpoints, and edge cases.

**Dependency flow:**

```
API
↓
Performance Service
↓
Snapshot Repository
↓
Snapshot Table
```

Performance logic uses persisted snapshots as source of truth. It does NOT call `market_data_service`, providers, or `get_portfolio_analytics()`.

**API contracts:** New endpoints only. No changes to existing endpoints.

**Not included:** Benchmark comparison, drawdown, volatility, Sharpe ratio, frontend work.

### Future — Cache Hardening (Planned)

**Goal:** Replace ad-hoc caching with the unified cache layer.

1. Migrate `market_data_service.py` caching to use `providers/cache.py`.
2. Migrate `portfolio_analytics.py` caching to use `providers/cache.py`.
3. Add request coalescing for high-traffic symbols.
4. Add rate-limit tracking per provider.
5. Add circuit breaker logic.

**Risk:** Medium. Touches existing cache behavior. Requires careful testing to ensure no regressions.

### Future — Health Monitoring & Background Jobs (Planned)

**Goal:** Add operational visibility and proactive cache warming.

1. Add provider health tracking (success/failure ring buffer).
2. Add cache-warming background job (pre-fetch popular symbols on startup and every 60s).
3. Add provider health check job (every 5 min).
4. Add logging for cache hit/miss ratios, rate limit status.

**Risk:** Low. Additive operational improvements.

### Future — News Integration

**Goal:** Add financial news feed.

1. Create `marketaux.py` (or use Finnhub news) adapter.
2. Create `news_service.py`.
3. Create new API endpoints and schemas.
4. Frontend integration.

**Risk:** Low. New feature, no existing behavior affected.

### Future — International Stocks & Advanced Features

**Goal:** Expand coverage beyond US markets.

1. Add Twelve Data adapter for international exchanges.
2. Add multi-provider fallback logic in service layer.
3. Consider WebSocket integration for real-time streaming.

**Risk:** Medium. Paid provider dependency. More complex provider routing.

---

### Implementation Timeline Summary

| Phase | Scope | Dependencies | Estimated Effort |
|---|---|---|---|
| **A — Foundation** | Provider layer, cache abstraction | None | ✅ PR #20 |
| **B — Finnhub** | Real stock data, provider registry | Phase A | ✅ PR #21 |
| **C — Reliability & Observability** | Structured logging, error classification | Phase B | ✅ PR #22 |
| **D — Portfolio Analytics** | Analytics engine, metrics, allocation | Phases A–C | ✅ PR #24 |
| **E — Portfolio Snapshots** | Snapshot model, history API, snapshot service | Phase D | ✅ PR #25 |
| **F — Portfolio Performance** | Performance returns, closest-snapshot logic | Phase E | ✅ PR #26 |
| **Cache Hardening** | Unified caching, coalescing, circuit breaker | Phase A | Planned |
| **Health & Monitoring** | Background jobs, logging | Phases A–D | Planned |
| **FRED** | Macroeconomic data | Phase A, FRED API key | Planned |
| **News** | News feed | Phase A | Future |
| **International** | Twelve Data, multi-provider | Phase A+B | Future |

Phases A–F have been implemented and merged. Future phases harden the system and extend coverage as the product grows.

---

## Implemented: Multi-Provider System (Phase B)

> This section documents the **implemented** provider architecture as of Phase B.
> It reflects the current codebase, not future speculative design.

### Provider Architecture

The provider abstraction layer is fully operational with multiple real data sources:

```
Frontend (Next.js)
    │
    │  GET /api/market-data/latest
    │  GET /api/market-data/history/{symbol}
    │  GET /api/market/prices
    ▼
FastAPI API Layer
    │
    ▼
Service Layer (market_data_service.py, market_data.py)
    │  Consumes only NormalizedQuote / NormalizedPriceHistory
    │  Provider-agnostic — never parses raw API payloads
    ▼
Provider Registry (providers/registry.py)
    │  Routes symbols to the correct provider adapter
    │
    ├── CoinGecko ──► BTC, ETH (crypto)
    ├── Finnhub   ──► AAPL, MSFT, GOOGL, ... (US stocks)
    └── Mock      ──► Unsupported/demo symbols
```

### Provider Ownership

| Provider | Asset Class | Symbols | API |
|---|---|---|---|
| **CoinGecko** | Cryptocurrency | BTC, ETH | `/simple/price`, `/coins/{id}/market_chart` |
| **Finnhub** | US Stocks | AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA | `/quote`, `/stock/candle` |
| **Mock** | Demo/Unsupported | Any symbol not covered by real providers | Deterministic PRNG (seed=42) |

### Provider Registry

The registry (`providers/registry.py`) is intentionally simple:

- **No plugin system.** No dynamic loading. No dependency injection.
- Routing is a linear check: first provider that `supports_symbol(sym)` wins.
- Check order: CoinGecko → Finnhub → Mock (fallback).
- `get_providers_for_symbols()` groups symbols by provider for batched API calls.
- `has_real_provider()` returns whether a symbol has a non-mock provider.

### Normalized Data Contracts

All providers produce the same internal types defined in `providers/types.py`:

- `NormalizedQuote` — symbol, name, price, change_24h, change_24h_pct, volume_24h, market_cap, **source**, timestamp
- `NormalizedPriceHistory` — symbol, name, interval, points (list of `NormalizedPricePoint`), **source**

**Why services only consume normalized objects:**
- Adding/replacing a provider never requires changes to service or API layers.
- The frontend schema is decoupled from any external API format.
- Source attribution is always available via the `source` field.

### Fallback Philosophy

**Real-provider symbols must never silently fall back to mock market prices.**

| Scenario | Behavior |
|---|---|
| Provider succeeds | Return real data (`source: "coingecko"` or `source: "finnhub"`) |
| Provider fails, stale cache exists | Return stale cached data (was real at some point) |
| Provider fails, no cache | Return HTTP 503 — **never mock** |
| Symbol has no real provider | Return mock data (`source: "mock"`) — explicit, not a fallback |

This prevents synthetic data from silently appearing as real market prices.

### Source Attribution

Every quote response includes a `source` field:

```json
{
  "BTC": {"price": 67500.0, "change_24h": 1.23, "source": "coingecko"},
  "AAPL": {"price": 190.50, "change_24h": 0.85, "source": "finnhub"},
  "XYZ": {"price": 42.00, "change_24h": 0.10, "source": "mock"}
}
```

Consumers can use this field to:
- Display data freshness indicators in the UI
- Filter out mock data in production dashboards
- Log/monitor which providers are active

---

## Implemented: Reliability & Observability (Phase C)

Phase C improves production readiness by adding structured logging, error classification, and rate-limit detection to all provider adapters. No API contracts, service interfaces, cache behavior, or registry logic were changed.

### Provider Failure Model

The system handles provider failures through a clear chain:

1. **Provider call succeeds** → data cached and returned
2. **Provider call fails** → error logged with structured fields, symbol skipped
3. **All symbols for a provider fail** → service checks stale cache
4. **Stale cache available** → stale data returned (was real at some point)
5. **No stale cache** → HTTP 503 "Market data temporarily unavailable"

Real-provider symbols (BTC, ETH, AAPL, etc.) **never** silently fall back to mock data. The mock provider is only used for symbols that have no real provider configured.

### Observability Model

All provider HTTP calls go through a `_request()` method that produces structured log lines with consistent fields:

**Success (DEBUG level):**
```
provider=finnhub endpoint=/quote status=success latency_ms=240
```

**Failure (ERROR level):**
```
provider=finnhub endpoint=/quote status=error error_type=http_error http_status=401 latency_ms=120
```

**Rate limit (WARNING level):**
```
provider=coingecko endpoint=/simple/price status=rate_limit latency_ms=85
```

#### Error Classification

Every provider failure is classified into one of four types:

| Error Type | Condition | Log Level |
|---|---|---|
| `rate_limit` | HTTP 429 response | WARNING |
| `timeout` | Request exceeded timeout | ERROR |
| `http_error` | Non-2xx response (excluding 429) | ERROR |
| `parse_error` | Response body is not valid JSON | ERROR |

This classification enables targeted operational response: rate limits may clear on their own, timeouts suggest network issues, HTTP errors suggest auth/config problems, and parse errors suggest provider API changes.

#### Latency Tracking

Every provider call records `latency_ms` (milliseconds, wall-clock). This enables:
- Identifying slow providers
- Detecting degradation trends
- Setting baseline performance expectations

#### Rate-Limit Detection

HTTP 429 responses are detected and logged separately from other HTTP errors. The log entry uses `status=rate_limit` for easy filtering. No automatic retry or cooldown is implemented yet — Phase C only detects and records the condition.

### Operational Goals

Phase C improves:
- **Production debugging** — structured fields make logs grep-friendly and parseable by log aggregators
- **Provider monitoring** — consistent format across all providers enables unified dashboards
- **System reliability** — all provider methods (`get_quotes`, `get_price_history`) catch exceptions and return safe defaults (empty list or None), never raising to the service layer

### Implementation Scope

Files modified:
- `providers/finnhub.py` — structured logging in `_request()`, `get_quotes()`, `get_price_history()`
- `providers/coingecko.py` — structured logging in `_request()`, `get_quotes()`, `get_price_history()`
- `tests/test_providers.py` — 11 new tests covering error logging, rate-limit detection, timeout classification, and failure resilience

No changes to: API responses, service layer interfaces, provider registry, cache behavior, or frontend.

---

## Implemented: Portfolio Analytics Engine (Phase D)

### Purpose

Phase D introduces a portfolio analytics layer that computes performance metrics from existing portfolio positions and normalized market data. The analytics engine sits between the API layer and the market data service, preserving the provider abstraction established in Phases A–C.

### Architecture

```
GET /api/portfolio/analytics
    │
    ▼
portfolio_analytics.py (orchestrator)
    │
    ├── DB: PortfolioTransaction → _normalize_positions() → PortfolioPosition
    │
    ├── market_data_service.get_current_prices_map(symbols)  ← single call
    │
    ├── metrics.py: calculate_portfolio_value, calculate_total_cost,
    │               calculate_total_pnl, calculate_return_pct
    │
    └── allocation.py: calculate_allocation, largest_position_weight, asset_count
```

### Key Design Decisions

- **Provider isolation preserved** — Analytics imports `market_data_service` only, never provider modules
- **Normalization inside analytics** — DB `asset_type="stock"` mapped to `"equity"` in the analytics layer; no DB schema changes
- **Pure calculation functions** — `metrics.py` and `allocation.py` are stateless, side-effect-free, trivially testable
- **Single market data call** — One `get_current_prices_map()` call per analytics request
- **Graceful degradation** — Missing prices: positions excluded from value/allocation but counted in diversification; empty portfolio returns zeros; market data failure caught and returns zero values

### Metrics Calculated

| Metric | Description |
|--------|-------------|
| `total_value` | Sum of (quantity × current price) for positions with available prices |
| `total_cost` | Sum of (quantity × avg cost) across all positions |
| `total_pnl` | `total_value - total_cost` |
| `return_pct` | `(total_pnl / total_cost) × 100` |
| `allocation` | Per-symbol weight = position value / total value (sorted descending, sums to 1.0) |
| `diversification.asset_count` | Number of active positions |
| `diversification.largest_position_pct` | Weight of the largest position |

### Implementation Scope

New files:
- `app/services/analytics/__init__.py`
- `app/services/analytics/metrics.py` — Pure financial calculation functions
- `app/services/analytics/allocation.py` — Allocation and diversification
- `app/services/analytics/portfolio_analytics.py` — Orchestrator
- `app/schemas/analytics.py` — Extended with `PortfolioAnalyticsResponse`
- `tests/test_portfolio_analytics.py` — 38 tests

Modified files:
- `app/api/v1/endpoints/portfolio.py` — Added `GET /analytics` endpoint

No changes to: existing API responses, service layer interfaces, provider registry, cache behavior, database models, or frontend.

---

## Implemented: Portfolio Snapshot & History API (Phase E)

**PR:** [#25](https://github.com/econclinic/financial-web-app/pull/25)

The analytics engine's outputs are now consumed by a snapshot system that records portfolio value over time.

### New files

- `app/models/portfolio_snapshot.py` — `PortfolioSnapshot` SQLAlchemy model
- `app/repositories/__init__.py`
- `app/repositories/portfolio_snapshot_repository.py` — Data access helpers (save, range query, recent query)
- `app/services/portfolio_snapshot_service.py` — Snapshot creation orchestrator (analytics → persistence)
- `tests/test_portfolio_snapshots.py` — 16 tests

### Modified files

- `app/schemas/analytics.py` — Added `SnapshotResponse`, `SnapshotHistoryPoint`, `SnapshotHistoryResponse`
- `app/api/v1/endpoints/portfolio.py` — Added `POST /snapshot` and `GET /history` endpoints
- `PROJECT_CONTEXT.md` — Phase E progress section
- `MARKET_DATA_ARCHITECTURE_PROPOSAL.md` — Phase E architecture and roadmap update

Snapshots reuse `get_portfolio_analytics()` directly. No direct provider access, no analytics duplication.

---

## Implemented: Portfolio Performance API (Phase F)

**PR:** [#26](https://github.com/econclinic/financial-web-app/pull/26)

Performance metrics are computed from persisted snapshots — no market data calls, no analytics recomputation.

### New files

- `app/services/performance/__init__.py`
- `app/services/performance/portfolio_performance_service.py` — Return computation with closest-snapshot-at-or-before logic
- `tests/test_portfolio_performance.py` — 20 tests

### Modified files

- `app/repositories/portfolio_snapshot_repository.py` — Added `get_latest_snapshot` and `get_closest_snapshot_at_or_before`
- `app/schemas/analytics.py` — Added performance response schemas
- `app/api/v1/endpoints/portfolio.py` — Added `GET /performance` and `GET /performance/history` endpoints
- `PROJECT_CONTEXT.md` — Phase F progress section
- `MARKET_DATA_ARCHITECTURE_PROPOSAL.md` — Phase F architecture and roadmap update

Dependency flow: API → Performance Service → Snapshot Repository → Snapshot Table.

---

## Summary

This architecture transforms the current monolithic market data integration (CoinGecko hardcoded + mock data) into a modular, provider-agnostic system that:

- **Decouples** the frontend from external providers entirely.
- **Normalizes** all external data into stable internal schemas.
- **Abstracts** each provider behind a common interface for easy swapping/addition.
- **Caches** aggressively with stale-while-revalidate and request coalescing.
- **Degrades gracefully** when providers fail (cached data → mock data → clear errors).
- **Scales** from free-tier development to paid production without architectural changes.
- **Preserves** all existing API contracts — the frontend continues working unchanged throughout the migration.
- **Computes** portfolio analytics (value, PnL, allocation, diversification) through a clean analytics layer built on the provider abstraction.
- **Tracks** portfolio value over time via lightweight snapshots that consume analytics outputs, with a history API for charting.
- **Computes** portfolio performance returns (7d, 30d, 90d, 1y) from stored snapshots without re-querying market data.
