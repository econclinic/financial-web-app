# Market Data Provider Research — Stage 3

> Research conducted May 2026 for the AI Finance WebApp project.
> This document evaluates external financial data providers for production integration.

---

## 1. Provider Evaluation

### 1.1 CoinGecko (Cryptocurrency)

| Attribute | Details |
|---|---|
| **Documentation** | https://docs.coingecko.com |
| **Pricing** | Demo (free): 30 calls/min, limited endpoints. Basic: $35/mo (100k credits, 250/min). Analyst: $129/mo (500k credits, 500/min, WebSocket). Lite: $499/mo (2M credits). Enterprise: custom. |
| **Free tier** | Demo API: 30 calls/min with API key (5–15/min without key). Limited to ~50 endpoints. No WebSocket. No webhook. 2-year historical data cap on free/Basic tiers. |
| **Rate limits** | Demo: 30/min. Basic: 250/min. Analyst+: 500/min. |
| **Real-time vs delayed** | Prices update every 1–2 minutes on all tiers. Not true tick-level real-time. WebSocket available on Analyst+ plans. |
| **Historical data** | Demo/Basic: limited. Analyst+: 10 years. Daily OHLC, market charts, volume. |
| **Reliability** | Excellent. Largest independent crypto data aggregator. High uptime. Well-maintained API with versioned endpoints. Enterprise tier offers 99.9% SLA. |
| **Integration complexity** | Low. Simple REST API, JSON responses, clear documentation. Already integrated in the project for BTC/ETH. |
| **WebSocket** | Analyst plan ($129/mo) and above. |
| **Licensing** | Free tier: personal/non-commercial. Paid tiers: commercial use allowed. Data redistribution requires Lite+ plan. |
| **Best for** | Cryptocurrency prices, market cap, 24h change, historical charts, coin metadata. |
| **Advantages** | Already integrated in the project. Comprehensive crypto coverage (14,000+ coins). No API key needed for basic usage. Well-documented. Reliable. |
| **Disadvantages** | Free tier is rate-limited and shrinking over time. No stock/forex data. Paid plans required for WebSocket and higher volume. Not truly real-time (1–2 min updates). |

---

### 1.2 Finnhub (Stocks, Forex, Crypto, News)

| Attribute | Details |
|---|---|
| **Documentation** | https://finnhub.io/docs/api |
| **Pricing** | Free: $0/mo. All-in-One: $3,500/mo (annual billing). |
| **Free tier** | 60 API calls/min. US stock data (OHLC 30+ years). WebSocket limited to 50 symbols. Company news (1 year). Basic fundamentals (US only). Personal use license. |
| **Rate limits** | Free: 60 calls/min. All-in-One: 900 calls/min (market), 300 calls/min (fundamental). |
| **Real-time vs delayed** | Free tier: real-time US stock quotes via REST. WebSocket: real-time trades for up to 50 symbols (free). All-in-One: unlimited WebSocket symbols. |
| **Historical data** | OHLC: 30+ years. Tick data: 30+ years (paid). News: 1 year free, 20 years paid. Earnings: 4 quarters free, 20+ years paid. |
| **Reliability** | Good. Established provider used by fintech startups. Some reports of WebSocket disconnections on free tier. REST API is stable. |
| **Integration complexity** | Low. Clean REST API. Python/JS SDKs available. WebSocket straightforward. |
| **WebSocket** | Yes. Free: 50 symbols. Paid: unlimited. Real-time trade data. |
| **Licensing** | Free: personal use only. Commercial use requires paid plan or explicit permission. |
| **Best for** | US stock quotes, company fundamentals, earnings, news, real-time WebSocket trades. |
| **Advantages** | Generous free tier (60 calls/min). Real-time US stock data. Covers stocks + forex + crypto + fundamentals + news in one API. WebSocket included free (limited). 30+ years of historical data. |
| **Disadvantages** | Massive jump from free to paid ($3,500/mo). Free tier is personal-use only. International stock coverage limited on free. WebSocket stability concerns on free tier. Global data requires paid plan. |

---

### 1.3 Twelve Data (Stocks, Forex, Crypto, ETFs)

| Attribute | Details |
|---|---|
| **Documentation** | https://twelvedata.com/docs |
| **Pricing** | Basic (free): $0. Grow: from $29/mo. Pro: from $79/mo. Ultra: $999/mo. Business plans: Venture $149/mo, Enterprise custom. |
| **Free tier** | 8 API credits/min (800/day). US markets, forex, crypto only. No international markets. Trial WebSocket (8 credits). No fundamentals. |
| **Rate limits** | Free: 8/min, 800/day. Grow: 55/min. Pro: 120/min. Ultra: 610/min. |
| **Real-time vs delayed** | Free: real-time for US, forex, crypto. Grow+: real-time for covered markets. International data may be delayed depending on exchange. |
| **Historical data** | Extensive. Time series from 1-min to monthly. 20+ years for many tickers. Technical indicators built-in (100+ indicators). |
| **Reliability** | Good. Well-documented API. Active development. Supports 50+ global exchanges on paid plans. |
| **Integration complexity** | Low. REST API with consistent response format. Official Python and JS SDKs. AI/MCP server integration available. |
| **WebSocket** | Trial on free. Full WebSocket requires Pro ($79/mo) or Venture ($149/mo). |
| **Licensing** | Free/Grow/Pro/Ultra: individual (personal/internal). Venture/Enterprise: commercial redistribution. |
| **Best for** | Multi-asset coverage (stocks + forex + crypto + ETFs). Technical indicators. Time series data. |
| **Advantages** | Covers stocks, forex, crypto, ETFs, commodities in one API. Built-in technical indicators (100+). Good documentation. Reasonable pricing progression. SDK support. 50+ global exchanges. |
| **Disadvantages** | Free tier is very limited (8/min, 800/day). International data only on Grow+. WebSocket requires Pro+. Business use requires Venture+. Credit-based system can be confusing. |

---

### 1.4 Alpha Vantage (Stocks, Forex, Crypto, Fundamentals)

| Attribute | Details |
|---|---|
| **Documentation** | https://alphavantage.co/documentation |
| **Pricing** | Free: $0. Premium tiers: $49.99/mo (75 calls/min), $99.99/mo (150 calls/min), $149.99/mo (300 calls/min), $249.99/mo (1200 calls/min). |
| **Free tier** | 25 requests/day. 5 calls/min. Covers most endpoints (stocks, forex, crypto, fundamentals, technical indicators, economic indicators). |
| **Rate limits** | Free: 25/day, 5/min. Premium: 75–1200 calls/min with no daily limit. |
| **Real-time vs delayed** | NASDAQ-licensed provider. Free tier: some endpoints return 15-min delayed data. Premium: real-time quotes. Bulk quotes premium-only. |
| **Historical data** | 20+ years of daily data. Intraday: 1-2 months on free, extended on premium. Adjusted for splits/dividends. Fundamental data: income statements, balance sheets, earnings. |
| **Reliability** | Mixed. NASDAQ-licensed (legitimate data source). API can be slow. Rate limiting is aggressive on free tier. Response format is verbose/non-standard (nested JSON with metadata keys). |
| **Integration complexity** | Medium. Single-endpoint design (`/query?function=...`) is unusual. Response format requires parsing nested time-series keys. No official SDK (community libraries exist). |
| **WebSocket** | No. REST only. |
| **Licensing** | Free: personal use. Premium: commercial use. NASDAQ-licensed for US data. |
| **Best for** | Budget-conscious stock data needs. Fundamental data (financials, earnings). Economic indicators. Technical indicators. |
| **Advantages** | Wide coverage (stocks, forex, crypto, commodities, economic indicators, technicals). NASDAQ-licensed. Comprehensive fundamental data. Premium plans are affordable vs competitors. |
| **Disadvantages** | Free tier severely limited (25 calls/day — unusable for production). No WebSocket. Slow API responses. Verbose response format. No official SDK. Reliability concerns (rate limits, timeouts). |

---

### 1.5 Polygon.io (Stocks, Options, Forex, Crypto)

| Attribute | Details |
|---|---|
| **Documentation** | https://polygon.io/docs |
| **Pricing** | Basic (free): $0. Starter: $29/mo. Developer: $79/mo. Advanced: $199/mo. |
| **Free tier** | 5 API calls/min. Delayed data. End-of-day only. Limited endpoints. Individual/non-professional use only. |
| **Rate limits** | Free: 5/min. Starter: unlimited calls. Developer+: unlimited. |
| **Real-time vs delayed** | Free/Starter: delayed (15-min). Developer: real-time WebSocket + tick data. Advanced: full real-time + SLA. |
| **Historical data** | 1+ year on free. Full historical on paid. Tick-level data (millisecond precision) on Developer+. Aggregates from 1-second to daily. |
| **Reliability** | Excellent. Institutional-grade infrastructure. Used by trading firms. Low-latency. SLA on Advanced plan. |
| **Integration complexity** | Low-Medium. Clean REST API. WebSocket well-documented. Official Python/JS clients. Response format is modern and consistent. |
| **WebSocket** | Starter+: WebSocket for aggregates. Developer+: tick-level streaming. Crypto WebSocket available. |
| **Licensing** | Free/Starter/Developer: individual non-professional use. Advanced+: professional use. Business plans for commercial redistribution. |
| **Best for** | High-quality US stock/options data. Tick-level historical data. Real-time WebSocket streaming. Institutional-grade needs. |
| **Advantages** | Institutional-quality data. Excellent documentation. WebSocket streaming. Tick-level precision. Covers stocks + options + forex + crypto. Unlimited API calls on paid plans. Fast response times. |
| **Disadvantages** | Free tier is barely usable (5/min, delayed). Professional licensing requires $199+/mo. Per-product pricing (stocks, options, indices are separate subscriptions). Gets expensive for multi-asset. Non-professional restriction on lower tiers. Recently rebranded to "Massive" — may cause confusion. |

---

### 1.6 FRED — Federal Reserve Economic Data (Macroeconomic)

| Attribute | Details |
|---|---|
| **Documentation** | https://fred.stlouisfed.org/docs/api/fred/ |
| **Pricing** | Completely free. No paid tiers. |
| **Free tier** | Full access to all 800,000+ economic data series. Free API key via email registration. |
| **Rate limits** | 2 requests/second (120/min). Exceeding returns HTTP 429. Temporary block possible for sustained abuse. |
| **Real-time vs delayed** | Not applicable — macroeconomic data is released on schedules (monthly, quarterly, annually). Data updated within hours of official release. |
| **Historical data** | Extensive. Many series go back 50+ years. GDP, unemployment, CPI, interest rates, money supply, housing, trade, etc. |
| **Reliability** | Excellent. Operated by the Federal Reserve Bank of St. Louis. Government infrastructure. Extremely stable. |
| **Integration complexity** | Low. Simple REST API. JSON and XML responses. Straightforward series/observations endpoint pattern. |
| **WebSocket** | No. REST only. Not needed — data updates infrequently. |
| **Licensing** | Public domain. No restrictions on use, redistribution, or commercial applications. |
| **Best for** | US macroeconomic indicators: GDP, CPI, unemployment rate, federal funds rate, treasury yields, money supply, housing starts, trade balance. |
| **Advantages** | Completely free with no paid tiers. 800,000+ data series. Public domain — no licensing concerns. Government-backed reliability. Decades of historical data. Simple API. |
| **Disadvantages** | US-focused only (limited international macro data). Low rate limit (2/sec). No real-time market data. Data updates are infrequent (tied to release schedules). No stock/crypto data. |

---

### 1.7 Marketaux (Financial News)

| Attribute | Details |
|---|---|
| **Documentation** | https://www.marketaux.com/documentation |
| **Pricing** | Free: $0. Starter: $19/mo. Professional: $49/mo. Enterprise: custom. |
| **Free tier** | 100 requests/day. 3 requests/min. News articles with entity tagging. Basic sentiment analysis. |
| **Rate limits** | Free: 3/min, 100/day. Starter: 10/min, 500/day. Professional: 30/min, 2000/day. |
| **Real-time vs delayed** | Near real-time news aggregation. Sources include major financial publications. |
| **Historical data** | Varies by plan. Free: recent articles only. Paid: historical archive access. |
| **Reliability** | Good. Focused product with clean API. Relatively new but actively maintained. |
| **Integration complexity** | Low. REST API with JSON responses. Clean entity/sentiment tagging. |
| **WebSocket** | No. REST only. |
| **Licensing** | Free tier: personal/non-commercial. Paid: commercial use. News content is aggregated (links to original sources). |
| **Best for** | Financial news aggregation. Sentiment analysis per entity/ticker. News-driven alerts. |
| **Advantages** | Built-in sentiment analysis. Entity recognition (tickers mapped to articles). Clean API design. Affordable paid plans. |
| **Disadvantages** | Limited free tier (100/day). Relatively new provider. No WebSocket for streaming news. Not as comprehensive as Bloomberg/Reuters alternatives. |

---

### 1.8 Yahoo Finance / yfinance (Stocks — Unofficial)

| Attribute | Details |
|---|---|
| **Documentation** | https://github.com/ranaroussi/yfinance (community) |
| **Pricing** | Free (unofficial scraping). No official API from Yahoo. |
| **Free tier** | Unlimited (unofficial — no API key needed). |
| **Rate limits** | Undocumented. Aggressive rate limiting and IP banning when abused. Typically ~2,000 requests/hour before throttling. |
| **Real-time vs delayed** | 15-minute delayed quotes. No real-time data. |
| **Historical data** | Extensive. Daily data going back decades. Intraday limited to recent months. Adjusted for splits/dividends. |
| **Reliability** | Poor for production. Breaks frequently when Yahoo changes their internal API. No SLA. No support. Single point of failure. IP bans possible. |
| **Integration complexity** | Low (Python library). Not suitable for backend REST adapter — no official API to call from server-side. |
| **WebSocket** | No. |
| **Licensing** | Gray area. Yahoo has no official free API. Using yfinance scrapes internal Yahoo endpoints. May violate Yahoo's ToS. Not suitable for commercial production use. |
| **Best for** | Personal research, prototyping, hobby projects. Not suitable for production applications. |
| **Advantages** | Free. Extensive coverage (global stocks, ETFs, mutual funds, crypto, forex). Easy Python integration. Large community. |
| **Disadvantages** | **Not production-suitable.** Unofficial/unsupported. Breaks frequently. Rate limits cause failures. No commercial license. Legal gray area. No customer support. IP blocking risk. |

---

### 1.9 Regional: Tehran Stock Exchange (TSETMC)

| Attribute | Details |
|---|---|
| **Data source** | http://tsetmc.com — official Tehran Stock Exchange website |
| **API** | No official REST API. Community-built scrapers/clients available. |
| **Community libraries** | `tsetmc-api` (Python, PyPI, MIT license, ~230 downloads/mo). `tse-client` (JavaScript/Node, npm, 40 GitHub stars). Both scrape TSETMC web pages. |
| **Data available** | Symbol info, live prices, market watch, day details, market map, historical OHLC. |
| **Rate limits** | Undocumented. TSETMC may throttle or block scrapers. |
| **Reliability** | Low. Scraper-based — breaks when TSETMC changes their website. Community-maintained with infrequent updates. |
| **Real-time** | Near real-time during market hours (scraped from live pages). |
| **Historical** | Available through TSETMC archive pages. Coverage varies. |
| **Licensing** | Community libraries are MIT-licensed, but scraping TSETMC may violate their terms. No official API license available. |
| **Feasibility assessment** | **Feasible for basic integration but risky for production.** No official API means ongoing maintenance burden. Suitable as an experimental/optional feature, not a primary data source. Scraper breakage is the main risk. Consider wrapping in a separate adapter with graceful degradation. |
| **Recommended approach** | If pursued: use `tsetmc-api` (Python) behind a dedicated backend adapter. Cache aggressively. Design for failure (return stale data or "unavailable" gracefully). Mark as experimental/beta in the UI. |

---

## 2. Structured Comparison Table

| Provider | Category | Free Tier | Rate Limit (Free) | Real-time | WebSocket | Historical | Pricing (Entry Paid) | Production Suitable | Integration Effort |
|---|---|---|---|---|---|---|---|---|---|
| **CoinGecko** | Crypto | 30/min (demo key) | 30/min | ~1-2 min updates | Analyst+ ($129/mo) | 10yr (paid) | $35/mo | Yes (paid) | Low (already integrated) |
| **Finnhub** | Stocks, Forex, Crypto, News | 60/min | 60/min | Yes (US stocks) | Yes (50 symbols free) | 30+ years | $3,500/mo | Yes (free for basic) | Low |
| **Twelve Data** | Stocks, Forex, Crypto, ETFs | 8/min, 800/day | 8/min | Yes (US, forex, crypto) | Pro+ ($79/mo) | 20+ years | $29/mo | Yes (paid) | Low |
| **Alpha Vantage** | Stocks, Forex, Crypto, Fundamentals | 25/day | 5/min | 15-min delayed (free) | No | 20+ years | $49.99/mo | Marginal | Medium |
| **Polygon.io** | Stocks, Options, Forex, Crypto | 5/min | 5/min | Developer+ ($79/mo) | Starter+ ($29/mo) | Full (paid) | $29/mo | Yes (paid) | Low-Medium |
| **FRED** | Macroeconomic | Full access | 2/sec (120/min) | N/A (scheduled) | No | 50+ years | Free | Yes | Low |
| **Marketaux** | Financial News | 100/day | 3/min | Near real-time | No | Limited | $19/mo | Yes (paid) | Low |
| **Yahoo/yfinance** | Stocks (unofficial) | Unlimited* | ~2000/hr* | 15-min delayed | No | Decades | Free | **No** | Low (Python) |
| **TSETMC** | Iran/TSE | Unofficial* | Unknown | Near real-time* | No | Available* | Free | **No (risky)** | Medium-High |

*\* = unofficial/scraper-based, not guaranteed*

---

## 3. Recommended Providers Per Category

### Cryptocurrency
**Primary: CoinGecko** (already integrated)
- Continue using CoinGecko for crypto data. Upgrade to Basic ($35/mo) or Analyst ($129/mo) when rate limits become a constraint.
- No competitive advantage to switching — CoinGecko has the best crypto coverage and is already integrated.

### Global Stocks
**Primary: Finnhub** (recommended) | **Alternative: Twelve Data**
- Finnhub's free tier (60 calls/min, real-time US quotes, WebSocket for 50 symbols) is the most generous for stock data and is production-usable for a growing app.
- Twelve Data is a strong alternative if broader international coverage is needed early, but requires paid plans faster ($29/mo) due to its limited free tier.
- Alpha Vantage is not recommended — 25 calls/day makes it unusable for any real-time or interactive application.
- Polygon.io is excellent quality but expensive for multi-asset coverage and has non-professional restrictions.
- Yahoo Finance / yfinance should not be used in production.

### Macroeconomic Indicators
**Primary: FRED** (no alternative needed)
- Completely free, 800,000+ series, government-backed reliability, public domain. No reason to look elsewhere for US macro data.

### Financial News
**Primary: Finnhub** (included) | **Alternative: Marketaux**
- Finnhub includes company news in its free tier (1 year of articles, real-time updates). This is sufficient for initial integration.
- Marketaux adds sentiment analysis and entity tagging at $19/mo if more sophisticated news features are needed later.

### Regional (Iran/TSE)
**Experimental: TSETMC via tsetmc-api**
- Feasible but risky. No official API — community scrapers only. Should be treated as experimental/beta if pursued. Wrap in a dedicated adapter with aggressive caching and graceful degradation.

---

## 4. Proposed Minimal Provider Stack for Stage 3

The goal is to minimize cost and complexity while covering the core asset classes needed for a professional financial dashboard.

| Priority | Provider | Category | Cost | Why |
|---|---|---|---|---|
| 1 | **CoinGecko** (existing) | Cryptocurrency | Free (demo) → $35/mo | Already integrated. Best crypto coverage. Upgrade when needed. |
| 2 | **Finnhub** | US Stocks + News | Free | 60 calls/min free tier. Real-time US stocks. WebSocket (50 symbols). Company news included. |
| 3 | **FRED** | Macroeconomic | Free | 800,000+ economic series. Government-backed. No cost, no licensing issues. |
| 4 | **Twelve Data** (later) | International Stocks + Forex | $29–79/mo | Add when international market coverage is needed. Better global exchange coverage than Finnhub free tier. |
| 5 | **Marketaux** (optional) | News + Sentiment | $19/mo | Add if sentiment analysis or advanced news features are requested. |

**Stage 3 total cost: $0/mo** (using CoinGecko demo + Finnhub free + FRED free)
**With first paid upgrade: $35/mo** (CoinGecko Basic for higher rate limits)

---

## 5. Suggested Provider Priority Order

1. **Finnhub** — Integrate first for US stock data. Replaces AAPL mock data immediately. Free tier is generous enough for production use at current scale.
2. **FRED** — Integrate second for macroeconomic indicators. Completely free. Adds a new data dimension (GDP, CPI, interest rates) to the analytics dashboard.
3. **CoinGecko upgrade** — Evaluate upgrading from demo to Basic tier when rate limits become a constraint (likely as user base grows).
4. **Twelve Data** — Integrate third when international stock market coverage is needed (European, Asian exchanges). Requires paid plan ($29/mo minimum).
5. **Marketaux** — Integrate when financial news features are on the product roadmap. Low priority for Stage 3.
6. **TSETMC** — Consider only if Iranian market data is explicitly requested. Treat as experimental.

---

## 6. Risks and Limitations

### Provider Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **CoinGecko free tier tightening** | Rate limits have decreased over time (was higher, now 5–30/min). May continue. | Budget for Basic ($35/mo) upgrade. Design with aggressive caching (60s minimum). |
| **Finnhub free tier is personal-use only** | Commercial production use technically violates ToS on free tier. | Contact Finnhub for a startup/commercial license if the app goes to production. Monitor for enforcement. |
| **Finnhub paid tier price jump** | $0 → $3,500/mo is a massive gap with no intermediate tier. | Use free tier as long as possible. Have Twelve Data as fallback for stocks. |
| **TSETMC scraper breakage** | Community scrapers break when TSETMC changes their website. | Wrap in adapter with graceful degradation. Cache aggressively. Mark as beta. |
| **Alpha Vantage rate limits** | 25 calls/day makes it essentially unusable for any interactive app. | Do not use as primary provider. Only suitable as supplementary data source for batch operations. |
| **Yahoo Finance legal risk** | Unofficial scraping. May violate ToS. IP bans. Frequent breakage. | Do not use in production. Period. |

### Architectural Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **Single provider dependency** | If one provider goes down or changes terms, the feature breaks. | Provider adapter pattern (already documented in DEVIN_GUIDE.md). Design each provider behind an interface so fallback/swap is straightforward. |
| **Rate limit exhaustion** | Multiple users hitting the app simultaneously could exhaust provider rate limits. | Backend request coalescing — cache responses server-side so 100 users requesting BTC price = 1 provider API call. Use existing 60s cache pattern. |
| **Data format inconsistency** | Different providers return different schemas, field names, precision, etc. | Normalize all provider data into internal schemas in the backend adapter layer before returning to API consumers. |
| **Cost scaling** | Provider costs grow with usage. Moving from free to paid is a discrete jump. | Start with free tiers. Design caching to minimize API calls. Monitor usage. Budget for tier upgrades proactively. |
| **Exchange licensing** | Real-time US stock data is exchange-regulated. Redistribution may require exchange licenses. | Use providers that are exchange-licensed (Finnhub, Alpha Vantage, Polygon). Do not redistribute raw exchange data without understanding licensing terms. |

### Strategic Recommendations

1. **Start free, scale paid.** The CoinGecko demo + Finnhub free + FRED stack provides substantial coverage at zero cost. Upgrade only when rate limits or data gaps become real constraints.
2. **Cache everything.** 60-second TTL for live prices, 5–15 minutes for historical/analytical data. This dramatically reduces provider API calls.
3. **One provider per category first.** Don't integrate multiple stock providers simultaneously. Get one working end-to-end, then add fallbacks.
4. **Design for provider failure.** Every provider call should handle timeouts, rate limits, and errors gracefully. Return cached data when possible, clear error messages when not.
5. **Monitor usage.** Track API call volumes per provider. Set up alerts before hitting rate limits. This prevents surprises and informs upgrade timing.

---

## 7. Summary

The recommended Stage 3 minimal provider stack is:

- **CoinGecko** (crypto — already integrated, free)
- **Finnhub** (US stocks + news — free tier, integrate first)
- **FRED** (macroeconomic — free, integrate second)

This stack covers cryptocurrency, US equities, and macroeconomic data at **zero monthly cost**, using legitimate, well-documented APIs with production-suitable reliability.

Future expansion to international stocks (Twelve Data), advanced news/sentiment (Marketaux), and regional markets (TSETMC) can be added incrementally as the product grows.
