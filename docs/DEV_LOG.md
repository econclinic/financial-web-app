# Development Log

## Phase I — Insights, UX Polish & Education Layer

### 2026-05-12

- Created Phase I documentation structure (`docs/PHASE_I_HOME_DASHBOARD.md`, `docs/DEV_LOG.md`)
- Wrote full Home Dashboard specification: layout, component structure, API dependencies, UX rules, RTL/LTR support
- Prepared Sprint 1 implementation plan for review
- Updated `PROJECT_CONTEXT.md` with Phase I overview

### 2026-05-12 — Sprint 1 Implementation

- Created data-fetching hooks: `usePortfolioPerformance`, `usePortfolioAllocation`
- Built 7 Home Dashboard components under `src/components/home/`:
  - `banner-slider.tsx` — auto-advancing promotional carousel with navigation dots
  - `portfolio-overview-card.tsx` — portfolio value + 7d return with color-coded change
  - `allocation-donut.tsx` — recharts PieChart with legend, linked to `/portfolio`
  - `live-market-prices.tsx` — vertical price list with 24h change indicators
  - `insights-carousel.tsx` — horizontal scroll-snap cards with placeholder insights
  - `video-section.tsx` — responsive YouTube embed
  - `article-carousel.tsx` — horizontal scroll-snap article cards with gradient thumbnails
- Added 44 translation keys (en + fa) for all Home Dashboard content
- Refactored `page.tsx` to compose all 7 sections in mobile-first layout
- Lint (0 errors) and build (TypeScript + Next.js) passing

### 2026-05-19 — Sprint 1 Review Feedback

- Replaced raw API error messages (e.g. "API error: 503") with user-friendly copy in both en and fa
- Added `home.marketPricesUnavailable` translation key for market prices error state
- Increased banner slider vertical padding on mobile (`py-10` → `py-16`) for better hero visual
- Added Gold, Silver, and S&P 500 (SPX) to backend market data layer (mock provider, service, quotes)
- Filtered Live Market Prices to show spec'd 5 assets: BTC, ETH, Gold, Silver, S&P 500

### 2026-05-19 — Sprint 1 Review Feedback (Round 2)

- Fixed InsightsCarousel card heights: added `h-[140px] flex flex-col` + `line-clamp-3` for uniform cards
- Fixed mock provider prices: switched from shared seeded RNG to per-symbol deterministic seeding so each asset gets distinct realistic prices that change hourly
- Confirmed AllocationDonut data flow is correct — it reflects the user's actual portfolio positions
- Added `USE_MOCK_ONLY = True` flag in `registry.py` — routes all symbols to mock provider for Sprint 1; set to `False` when real API keys are configured
- Added `test_mock_only_routes_all_to_mock` test; existing routing tests patched to verify real routing logic is preserved
