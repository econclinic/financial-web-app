# Phase I — Home Dashboard Specification

## Overview

The Home Dashboard is the primary landing experience for authenticated users. It consolidates portfolio analytics, market data, educational content, and actionable insights into a single mobile-first page that replaces the current dashboard.

---

## Page Layout (Mobile First)

Sections are rendered in this exact order on mobile. Desktop may rearrange into a multi-column grid but must preserve section priority.

| # | Section | Data Source | Interactive |
|---|---------|-------------|-------------|
| 1 | Banner Slider | Static / CMS | Swipeable, tappable |
| 2 | Portfolio Overview + Benchmark | `GET /api/portfolio/performance?range=` | Tappable → deep link |
| 3 | Portfolio Allocation Donut | `GET /api/portfolio/allocation` | Tappable → allocation page |
| 4 | Live Market Prices | `GET /api/market/quotes` | Tappable → asset detail |
| 5 | Insights Cards | `GET /api/portfolio/contribution`, `GET /api/portfolio/performers`, `GET /api/portfolio/allocation` | Horizontal swipe |
| 6 | Video Section | Static YouTube embed | Play in-page |
| 7 | Articles / News | Static / CMS | Horizontal swipe, "Read More" |

---

## Section Specifications

### 1. Banner Slider

- Promotional banners displayed as a horizontally swipeable carousel
- Auto-advances every 5 seconds; pauses on user interaction
- Each banner is tappable and opens a product/course page (internal link or external URL)
- Supports 2–6 banners
- Images should be responsive (16:9 aspect ratio on mobile, wider on desktop)
- Renders above the fold on all viewports

### 2. Portfolio Overview + Benchmark Comparison

A compact summary card showing:

- **Portfolio value** — current total value (from performance API `ending_value`)
- **Daily change** — absolute and percentage change (from performance API with `range=7d` or analytics overview)
- **Benchmark comparison** — S&P 500 return over the same period, shown side-by-side
- Tapping the card navigates to the full portfolio analytics page (`/dashboard/analytics`)

**API dependencies:**
- `GET /api/portfolio/performance?range=7d` — for portfolio return
- Benchmark data from `lib/benchmark-data.ts` (existing static/mock source)

### 3. Allocation Chart (Donut)

- Donut/ring chart showing portfolio allocation by asset class
- Powered by `GET /api/portfolio/allocation` API
- Each segment shows asset class label and percentage weight
- Tapping the chart navigates to the full allocation page (future route or `/portfolio`)
- Empty state: show "No positions" placeholder
- Uses `recharts` PieChart component (already a project dependency)

**API dependencies:**
- `GET /api/portfolio/allocation` — `assets[]` with `symbol`, `value`, `weight`

### 4. Live Market Prices

Vertical list showing 5 default assets:

| Asset | Symbol |
|-------|--------|
| Bitcoin | BTC |
| Ethereum | ETH |
| Gold | GOLD |
| Silver | SILVER |
| S&P 500 | SPX |

Each row displays:
- Asset name and symbol
- Current price
- 24h change (absolute + percentage)
- Color coding: green for positive, red for negative

Tapping a row opens the asset detail / price chart view.

**API dependencies:**
- `GET /api/market/quotes` — existing market data endpoint

### 5. Insights Cards (Horizontal Swipe)

Horizontally scrollable card carousel. Each card represents one actionable insight derived from portfolio analytics.

Example insight types:

| Insight | Source API | Example Text |
|---------|-----------|-------------|
| Diversification | `/api/portfolio/exposure` | "Your portfolio is 80% crypto — consider diversifying" |
| Top Performer | `/api/portfolio/performers` | "ETH is your best performer at +25%" |
| Concentration Risk | `/api/portfolio/allocation` | "AAPL represents 45% of your portfolio" |
| Max Drawdown | `/api/portfolio/performance?range=30d` | "Your portfolio had a max drawdown of -8.2% this month" |

Card structure:
- Icon or emoji indicator
- Insight title (bold)
- Insight description (1–2 sentences)
- Optional CTA button ("View Details")

### 6. Video Section

- Embedded YouTube player for curated educational content
- Single featured video displayed at a time
- Responsive embed (16:9 aspect ratio)
- Video title and brief description shown below the embed
- Content is statically configured (video ID + metadata)

### 7. Articles / News (Horizontal Swipe)

Horizontally scrollable card carousel for educational articles and market news.

Each card contains:
- Thumbnail image
- Article title
- Short summary (2–3 lines, truncated)
- "Read More" button → opens article URL (external link in new tab)

Content is statically configured for Sprint 1 (hardcoded article list). Future phases may integrate a CMS or RSS feed.

---

## Mobile-First Layout Rules

1. **Single column on mobile** (< 768px) — all sections stack vertically in the order above
2. **Two-column grid on tablet** (768px–1024px) — Portfolio Overview and Allocation side-by-side; other sections full-width
3. **Multi-column on desktop** (> 1024px) — flexible grid with sections 2+3 in a row, section 4 as sidebar, sections 5–7 full-width
4. **Avoid long vertical scrolling** — use horizontal swipe for Insights and Articles instead of vertical lists
5. **Touch-first interactions** — swipe gestures, large tap targets (min 44px), no hover-dependent UI
6. **Responsive images** — use `next/image` with proper `sizes` and `priority` for above-the-fold images
7. **Skeleton loading** — show shimmer/pulse placeholders while API data loads (consistent with existing `MarketDataSection` pattern)

---

## RTL / LTR Support

- All text and layout must support both LTR (English) and RTL (Farsi/Persian)
- Use Tailwind's `ltr:` and `rtl:` prefixes for directional spacing (already established in the codebase)
- Carousel/swipe direction follows document direction
- Icons that imply direction (arrows) must flip in RTL
- All user-facing strings must go through the `useLocale()` / `t()` translation system
- New translation keys must be added to `lib/i18n/translations.ts` for both `en` and `fa`

---

## Deep Linking

Every section must support a stable anchor for deep linking:

| Section | Anchor | Navigation Target |
|---------|--------|-------------------|
| Banner | `#banners` | — |
| Portfolio Overview | `#portfolio-overview` | `/dashboard/analytics` |
| Allocation | `#allocation` | `/portfolio` |
| Market Prices | `#market-prices` | Asset detail view |
| Insights | `#insights` | Varies per insight |
| Video | `#education` | — |
| Articles | `#articles` | External article URL |

---

## Component Structure

```
src/
├── app/
│   └── page.tsx                          # Home Dashboard page (updated)
├── components/
│   └── home/
│       ├── banner-slider.tsx             # Promotional banner carousel
│       ├── portfolio-overview-card.tsx    # Portfolio value + benchmark
│       ├── allocation-donut.tsx          # Donut chart (recharts PieChart)
│       ├── live-market-prices.tsx        # Vertical price list
│       ├── insights-carousel.tsx         # Horizontal insight cards
│       ├── video-section.tsx             # YouTube embed
│       └── article-carousel.tsx          # Horizontal article cards
└── lib/
    └── insights.ts                       # Insight generation logic
```

---

## API Dependencies Summary

| Endpoint | Used By | Auth Required |
|----------|---------|---------------|
| `GET /api/portfolio/performance?range=7d` | Portfolio Overview | Yes |
| `GET /api/portfolio/allocation` | Allocation Donut, Insights | Yes |
| `GET /api/portfolio/contribution` | Insights | Yes |
| `GET /api/portfolio/performers` | Insights | Yes |
| `GET /api/portfolio/exposure` | Insights | Yes |
| `GET /api/market/quotes` | Live Market Prices | No |

---

## UX Interaction Rules

1. **Loading states** — every section that depends on API data shows a skeleton loader
2. **Error states** — graceful degradation; show "Unable to load" with retry option, not a crash
3. **Empty states** — sections with no data (e.g., empty portfolio) show helpful prompts ("Add your first transaction")
4. **Transitions** — smooth scroll between sections; carousel transitions use CSS transforms
5. **Accessibility** — ARIA labels on interactive elements, keyboard navigation for carousels, focus management
6. **Performance** — lazy-load below-the-fold sections; prioritize above-the-fold content (banner + portfolio overview)

---

## Sprint 1 Scope

Sprint 1 focuses on **layout skeleton and component structure** — not advanced analytics logic.

### Included in Sprint 1

- Home page layout skeleton with all 7 sections
- Mobile-first responsive layout (single column → grid)
- Banner slider component (with placeholder images)
- Portfolio overview card (connected to performance API)
- Allocation donut placeholder (connected to allocation API)
- Live market price widget (connected to existing market data)
- Insights card layout (with static example insights)
- Video embed container (with placeholder video)
- Article card layout (with static placeholder articles)
- Skeleton loading states for all API-dependent sections
- RTL/LTR support for all new components
- Translation keys for all new user-facing strings

### Deferred to Sprint 2+

- Dynamic insight generation from real analytics data
- CMS integration for banners and articles
- Advanced benchmark comparison with real S&P 500 data
- Article/news feed from external sources
- Video content curation system
- Analytics tracking / event logging
- Performance optimization (intersection observer lazy loading)
