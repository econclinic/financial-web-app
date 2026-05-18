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
