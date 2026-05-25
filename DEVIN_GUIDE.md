# DEVIN_GUIDE.md

> Persistent onboarding memory for Devin sessions and future contributors.
> This document preserves architectural consistency, product direction, development workflow, and UI/UX standards across all sessions.

---

## 1. Project Overview

**AI Finance WebApp** is a modular financial web application that provides a unified dashboard for monitoring market data, managing portfolios, tracking watchlists, setting price alerts, and viewing analytics.

- **Target audience:** Retail investors, finance enthusiasts, and users who want a single platform to track and analyse financial markets.
- **Current maturity:** Post-MVP — Stage 3 product hardening complete through Phase I. The initial roadmap (Phases 1–7) has been fully delivered, covering authentication, market data, portfolio management, watchlists, price alerts, notifications, analytics, and a complete UI/UX transformation. Stage 3 (Phases A–I) delivered a multi-provider market data system (CoinGecko + Finnhub + mock), portfolio analytics engine with performance tracking and allocation analysis, and a 7-section mobile-first Home Dashboard with insights and educational content.
- **Long-term product direction:** The platform is evolving from a functional prototype into a professional-grade financial dashboard. Future stages will expand real-time market data coverage, introduce dynamic analytics insights, educational content management, financial news integrations, alert automation, and professional branding — all built on top of the existing modular architecture.

The project has transitioned from MVP development into active product professionalization. All new work must reflect production-quality standards.

---

## 2. Core Product Philosophy

These principles guide all development decisions in this project:

- **Simplicity over unnecessary complexity.** Choose the simplest solution that meets the requirement. Avoid abstractions, patterns, or libraries that don't provide clear, immediate value.
- **Preserve existing architecture whenever possible.** The current codebase has been built through iterative, reviewed phases. Extend and improve — don't rewrite without strong justification.
- **Avoid over-engineering.** Build for today's requirements. Do not introduce speculative infrastructure for hypothetical future needs.
- **Prioritize clean UX.** Every interaction should feel intentional and polished. Avoid cluttered interfaces, confusing flows, or unnecessary UI elements.
- **Responsive-first design.** All UI changes must work across mobile, tablet, and desktop. Mobile is not an afterthought — it is the primary design target.
- **RTL support is mandatory.** The application supports both English (LTR) and Persian/Farsi (RTL). All new UI must work correctly in both directions. Use Tailwind `ltr:`/`rtl:` variants where needed.
- **Backend-driven integrations.** External data providers (market data, news, etc.) must be integrated through the backend. The frontend should never directly call third-party APIs.
- **Production-oriented mindset.** Every change should be written as if it's shipping to production. Consider error handling, edge cases, loading states, and accessibility.

---

## 3. Development Workflow

Every Devin session and contributor should follow this workflow:

1. **Always read `PROJECT_CONTEXT.md`** before making any changes. This is the single source of truth for the project's current state, architecture, and module documentation.
2. **Always read `DEVIN_GUIDE.md`** (this file) to understand product direction, architectural principles, and development standards.
3. **Understand the current branch** before making changes. Confirm which branch you are on and what its relationship is to `main`. Never commit directly to `main`.
4. **No drive-by refactoring.** Keep changes scoped to the task at hand. Do not modify unrelated code, rename unrelated variables, or restructure unrelated files — even if you believe the change is an improvement. If you notice something that needs improvement outside your current scope, document it in the PR description or open a separate issue. The only exception is fixing a direct bug that blocks your current task.
5. **Keep pull requests focused and small.** Each PR should address a single concern or feature. Avoid mixing unrelated changes in a single PR.
6. **Explain architectural decisions clearly.** When making non-obvious technical choices, document the reasoning in the PR description or code comments.
7. **Documentation is part of "Done".** No task is complete until documentation is updated. Specifically:
   - **`PROJECT_CONTEXT.md`** must be updated when adding new modules, changing architecture, completing phases, or modifying API contracts.
   - **`DEVIN_GUIDE.md`** must be updated when architectural principles, development standards, or product direction change.
   - **`docs/DEV_LOG.md`** must be updated with a dated entry for every meaningful code change.
   - If a phase is completed, its status must be updated in both `PROJECT_CONTEXT.md` (roadmap table and phase section) and `MARKET_DATA_ARCHITECTURE_PROPOSAL.md` (implementation timeline).
8. **Preserve backward compatibility when possible.** Avoid breaking existing functionality, API contracts, or data formats unless explicitly required and approved.

---

## 4. Architecture Principles

### Frontend

- **React + Tailwind architecture.** The frontend uses Next.js 16 (App Router) with React 19 and Tailwind CSS v4. All styling should use Tailwind utility classes and follow the existing design token system.
- **Reusable UI components.** Favor building shared components in `components/shared/` or `components/ui/` over duplicating UI logic across pages.
- **Responsive layouts.** All pages must be responsive. Use mobile-first breakpoints (`sm:`, `md:`, `lg:`) consistently.
- **Avoid duplicated UI logic.** If the same pattern appears on multiple pages (e.g., skeleton loaders, empty states, error banners), extract it into a shared component.
- **Maintain loading and skeleton states.** Every page that fetches data should show an appropriate loading state (skeleton loader or spinner) and an empty state when no data is available.
- **Maintain RTL compatibility.** All new UI must render correctly in both LTR and RTL modes. Test with both English and Farsi locales.

### Backend

- **Backend abstraction layer for external APIs.** All external data sources (market data, news, etc.) must be accessed through backend services. The frontend calls only internal API endpoints.
- **Frontend must not directly call market providers.** This ensures consistent caching, rate limiting, error handling, and data normalization.
- **Provider adapter pattern preferred.** Each external provider should be wrapped in an adapter that conforms to an internal interface. This allows swapping providers without changing downstream service or API code.
- **Normalize external data formats.** External API responses must be transformed into a consistent internal schema before being returned to the frontend.
- **Maintain clean API contracts.** All endpoints should have well-defined Pydantic request/response schemas. Do not return raw external API responses to the frontend.

### General

- **Avoid unnecessary dependencies.** Before adding a new library, check if the functionality can be achieved with existing tools or a small amount of custom code.
- **Prefer maintainability over cleverness.** Write code that is easy to read, understand, and modify. Avoid clever shortcuts that sacrifice clarity.
- **Preserve the current folder structure unless necessary.** The project has a well-established directory layout. Only restructure if there is a clear, justified reason.

---

## 5. UI/UX Direction

The application should convey a **modern, professional financial dashboard** feel. All UI work should aim for:

- **Smooth responsive behavior.** Transitions between breakpoints should be clean. No layout jumps, overflow, or misaligned elements.
- **Mobile-first polish.** Design for small screens first, then enhance for larger viewports. Mobile responsiveness is considered critical.
- **Clear visual hierarchy.** Important information (prices, P&L, alerts) should be immediately visible. Use font weight, size, color, and spacing to guide the user's eye.
- **Clean spacing system.** Maintain consistent padding, margins, and gaps. Follow the existing patterns in the codebase (e.g., `px-4 py-6 sm:px-6 sm:py-8`, `gap-3`, `space-y-3`).
- **Consistent typography.** Use the established font stack (Inter + Vazirmatn) and follow the heading/body size conventions defined in the design tokens.
- **Avoid cluttered interfaces.** Every element on screen should earn its place. Remove unnecessary decorations, redundant labels, or excessive information density.
- **Maintain accessibility where possible.** Use semantic HTML, appropriate ARIA attributes, sufficient color contrast, and keyboard-navigable interactive elements.

### Non-Negotiable: Zero Horizontal Overflow

**The app must have NO horizontal scroll on mobile devices (320px to 480px viewport width).** This is a hard requirement — not a guideline.

Any new layout, component, or section must be tested for `overflow-x` issues before submission. Specific rules:

- **Carousels and horizontal scroll containers** must be wrapped in a constrained parent with `w-full max-w-full overflow-hidden`. The inner scroll container uses `overflow-x-auto`.
- **Cards inside carousels** must use fixed widths (`w-[300px] shrink-0`) — never content-driven `min-w-*` sizing, which causes unpredictable expansion.
- **Page-level safety net:** The `<main>` element should include `overflow-x-hidden` to prevent any child from causing page-level horizontal scroll.
- **Verification method:** Before submitting any layout change, verify at viewport widths of 320px, 375px, 414px, 768px, and 1024px that `document.body.scrollWidth === document.body.clientWidth` (i.e., zero overflow).
- **Flex containers:** Use `min-w-0` on flex children that may contain wide content to prevent flex items from expanding beyond their container.

---

## 6. Market Data Strategy

### Current State (Post-Phase I)

The market data system has been fully architected through a **Provider Adapter Layer** (Phases A–C) with two real providers and a mock fallback:

| Provider | Asset Class | Status | Symbols |
|---|---|---|---|
| **CoinGecko** | Cryptocurrency | Integrated (adapter complete) | BTC, ETH |
| **Finnhub** | US Stocks | Integrated (adapter complete) | AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA |
| **Mock** | Development fallback | Active (Sprint 1 default) | All symbols when `USE_MOCK_ONLY=True` |

**Current routing:** During Sprint 1, all symbols route to the mock provider (`USE_MOCK_ONLY = True` in `backend/app/providers/registry.py`). This is a temporary development convenience — set to `False` once real API keys are configured. The mock provider uses per-symbol deterministic seeding for realistic price variation.

**Priority:** Real-time integration via the Provider Adapter pattern is the target state. Mock data is strictly a development fallback, not a production strategy. All new provider work should prioritize connecting real data sources.

- **Price history:** Mock data for all symbols. Real historical data integration is pending.
- **Benchmark data:** Client-side mock data generated via seeded PRNG.
- **Home Dashboard:** Consumes `/api/portfolio/performance`, `/api/portfolio/allocation`, and `/api/market-data/latest` — provider-agnostic.

### Implemented Architecture

```
Frontend → FastAPI API Layer → Service Layer → Provider Registry → Adapters
                                                    │
                                                    ├── CoinGecko (crypto)
                                                    ├── Finnhub (stocks)
                                                    └── Mock (fallback)
```

All providers implement the `MarketDataProvider` Protocol defined in `providers/base.py`. The service layer consumes only normalized types (`NormalizedQuote`, `NormalizedPriceHistory`). See `MARKET_DATA_ARCHITECTURE_PROPOSAL.md` for full details.

### Future Direction

| Provider | Focus | Status |
|---|---|---|
| **Twelve Data** | International stock/forex/crypto time series | Planned |
| **FRED** | Macroeconomic data, economic indicators | Planned |
| **Marketaux** | Financial news, sentiment analysis | Future |

### Integration Principles

- **Real-time data is the priority.** Mock data exists only as a development fallback. All new provider work should connect real data sources. Never treat mock data as acceptable for production.
- **Provider abstraction is mandatory.** Every provider must implement the `MarketDataProvider` Protocol. This allows adding, removing, or replacing providers without touching service or API layer code.
- **Caching is required.** All provider responses are cached in-memory with per-key TTL (60 seconds for live quotes, 15 minutes for historical data). Redis is planned for production multi-worker deployments.
- **Rate limit awareness.** Every integration must respect the provider's rate limits. HTTP 429 responses are detected and logged. Fallback to cached data is automatic.
- **Reliability requirements.** Provider failures are handled gracefully: return cached data when available, return clear error responses when not. Real-provider symbols never silently fall back to mock data — they get stale cache or HTTP 503.

---

## 7. Asset Management Rules

Branding and media assets should be organized under the `public/` directory with a clear structure:

```
/public/branding     # Logos, favicons, brand marks
/public/banners      # Promotional banners, hero images
/public/courses      # Course thumbnails, educational materials
/public/media        # General media assets (videos, screenshots, misc)
```

**Proprietary assets may include:**

- Logos and brand marks
- Promotional banners and hero images
- Educational thumbnails and course cover images
- Promotional graphics and marketing materials
- Videos and animated content
- Course materials and learning resources

All asset filenames should be descriptive and use kebab-case (e.g., `logo-dark-horizontal.svg`, `course-thumbnail-intro-to-trading.png`).

---

## 8. Pull Request Standards

All pull requests should follow these standards:

- **Focused scope.** Each PR should address a single feature, fix, or improvement. Do not bundle unrelated changes.
- **Clean commit history.** Use descriptive commit messages that explain what changed and why. Avoid generic messages like "fix" or "update".
- **Clear PR descriptions.** Include:
  - A short summary of what the PR does.
  - Any architectural decisions or trade-offs made.
  - Notes about schema, API, or dependency changes.
- **Include manual testing notes.** Describe what was tested manually and what the reviewer should verify.
- **Include screenshots for UI changes.** Before/after screenshots or recordings help reviewers understand visual changes quickly.
- **Avoid mixing unrelated concerns.** If you discover a bug or improvement opportunity outside your current scope, open a separate issue or PR for it.

---

## 9. Completed Phases

This section tracks the implementation status of all project phases. It must stay in sync with `PROJECT_CONTEXT.md`.

### MVP Roadmap (Phases 1–7) — Complete

| Phase | Scope | PR |
|---|---|---|
| Phase 1 | Design Tokens + Theme System | #12 |
| Phase 2 | Typography + Font Loading | #13 |
| Phase 3 | Responsive Layouts | #14 |
| Phase 4 | i18n + RTL Support | #15 |
| Phase 5 | Smart Summary Card | #16 |
| Phase 6 | Benchmark Comparison | #17 |
| Phase 7 | Alerts Upgrade + UX Polish | #18 |

### Stage 3 — Product Hardening (Phases A–I) — Complete

| Phase | Scope | PR |
|---|---|---|
| Phase A | Provider Abstraction Layer | #20 |
| Phase B | Finnhub Integration + Provider Registry | #21 |
| Phase C | Reliability & Observability | #22 |
| Phase D | Portfolio Analytics Engine | #24 |
| Phase E | Portfolio Snapshot & History API | #25 |
| Phase F | Portfolio Performance API | #26 |
| Phase G | Portfolio Allocation & Exposure API | #27 |
| Phase H | Portfolio Performance Engine | #28 |
| Phase I | Home Dashboard (Sprint 1) | #29 |

### Current Status

The project is in the **Professionalization and Refactoring** stage. All MVP and Stage 3 phases are complete. Future work focuses on expanding real-time data coverage, dynamic analytics insights, content management, and infrastructure hardening.

---

## 10. Long-Term Product Direction

The platform's long-term vision extends beyond the current implementation into a comprehensive financial tools platform. Future stages may include:

- **Live market systems** — real-time price streaming, WebSocket connections, multi-provider data aggregation.
- **Dynamic insights** — auto-generated portfolio insights from contribution, performer, and allocation APIs.
- **Advanced watchlists** — custom grouping, notes, tags, alerts integration, and comparison views.
- **Portfolio management** — edit/delete positions, multi-portfolio support, transaction import from brokerages.
- **Educational content management** — CMS-driven courses, tutorials, learning paths, and curated video content.
- **Financial news integrations** — curated news feeds, sentiment analysis, and event-driven alerts.
- **Analytics infrastructure** — advanced charting, technical indicators, custom dashboards, and data export.
- **Alert automation** — recurring alerts, multi-condition triggers, notification channels (email, push, SMS).
- **Professional branding systems** — white-label capabilities, custom themes, branded content delivery.

Each of these areas will be developed incrementally, following the track-based organization defined in Stage 3.

---

## 11. Session Initialization Rule

> **Mandatory for every Devin session and contributor.**

Before starting any implementation work, every Devin session must first read:

1. **`PROJECT_CONTEXT.md`** — for the current state of the project, module documentation, and architecture reference.
2. **`DEVIN_GUIDE.md`** — for product direction, development standards, and architectural principles.

**No implementation should begin before context synchronization.**
