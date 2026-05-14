# DEVIN_GUIDE.md

> Persistent onboarding memory for Devin sessions and future contributors.
> This document preserves architectural consistency, product direction, development workflow, and UI/UX standards across all sessions.

---

## 1. Project Overview

**AI Finance WebApp** is a modular financial web application that provides a unified dashboard for monitoring market data, managing portfolios, tracking watchlists, setting price alerts, and viewing analytics.

- **Target audience:** Retail investors, finance enthusiasts, and users who want a single platform to track and analyse financial markets.
- **Current maturity:** Completed MVP — Entering Product Professionalization Stage. The initial roadmap (Phases 1–7) has been fully delivered, covering authentication, market data, portfolio management, watchlists, price alerts, notifications, analytics, and a complete UI/UX transformation (theming, typography, responsive layouts, i18n/RTL, skeleton loaders, toast notifications, and empty states).
- **Long-term product direction:** The platform is evolving from a functional prototype into a professional-grade financial dashboard. Future stages will introduce live market data integrations, advanced analytics, educational content systems, financial news, alert automation, and professional branding — all built on top of the existing modular architecture.

The project has transitioned from MVP development into product professionalization. All new work should reflect production-quality standards.

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
4. **Avoid unrelated refactors.** Keep changes scoped to the task at hand. If you notice something that needs improvement outside your current scope, document it rather than fixing it in the same PR.
5. **Keep pull requests focused and small.** Each PR should address a single concern or feature. Avoid mixing unrelated changes in a single PR.
6. **Explain architectural decisions clearly.** When making non-obvious technical choices, document the reasoning in the PR description or code comments.
7. **Document important changes.** Update `PROJECT_CONTEXT.md` when adding new modules, changing architecture, or completing major milestones.
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

---

## 6. Market Data Strategy

### Current State

- **Crypto (BTC, ETH):** Real-time prices from CoinGecko public API (no key required). Includes 24h change percentage.
- **Stocks (AAPL):** Mock data with deterministic jitter. Not connected to a real provider.
- **Price history:** Mock data for all symbols. Real historical data integration is pending.
- **Benchmark data:** Client-side mock data generated via seeded PRNG.

### Future Direction

Market data integrations will expand to cover additional asset classes and real-time data sources.

**Preferred providers currently under evaluation:**

| Provider | Focus |
|---|---|
| **CoinGecko** | Cryptocurrency prices, market data, historical charts |
| **Finnhub** | Stock quotes, company profiles, financial news |
| **Twelve Data** | Stock/forex/crypto time series, technical indicators |
| **FRED** | Macroeconomic data, economic indicators, interest rates |

### Integration Principles

- **Provider abstraction philosophy.** Each provider should be wrapped in an adapter class or module that implements a common interface. This allows adding, removing, or replacing providers without touching service or API layer code.
- **Caching expectations.** All provider responses must be cached (in-memory for MVP, Redis or equivalent for production). Cache TTLs should balance freshness against rate limits — typically 60 seconds for live quotes, 5–15 minutes for historical data.
- **Rate limit awareness.** Every integration must respect the provider's rate limits. Implement request throttling, backoff strategies, and fallback to cached data when limits are approached.
- **Reliability requirements.** Provider failures must be handled gracefully. Return cached data when available, return clear error responses when not, and never let a provider outage crash the application.

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

## 9. Long-Term Product Direction

The platform's long-term vision extends beyond the current MVP into a comprehensive financial tools platform. Future stages may include:

- **Live market systems** — real-time price streaming, WebSocket connections, multi-provider data aggregation.
- **Advanced watchlists** — custom grouping, notes, tags, alerts integration, and comparison views.
- **Portfolio tracking** — historical performance tracking, multi-portfolio support, transaction import from brokerages.
- **Educational content systems** — courses, tutorials, learning paths, and embedded educational media.
- **Financial news integrations** — curated news feeds, sentiment analysis, and event-driven alerts.
- **Analytics infrastructure** — advanced charting, technical indicators, custom dashboards, and data export.
- **Alert automation** — recurring alerts, multi-condition triggers, notification channels (email, push, SMS).
- **Professional branding systems** — white-label capabilities, custom themes, branded content delivery.

Each of these areas will be developed incrementally, following the track-based organization defined in Stage 3.

---

## 10. Session Initialization Rule

> **Mandatory for every Devin session and contributor.**

Before starting any implementation work, every Devin session must first read:

1. **`PROJECT_CONTEXT.md`** — for the current state of the project, module documentation, and architecture reference.
2. **`DEVIN_GUIDE.md`** — for product direction, development standards, and architectural principles.

**No implementation should begin before context synchronization.**
