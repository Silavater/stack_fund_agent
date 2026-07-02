# Data Sources (real connectors)

> Adapted from AZNitro/tw-stock-agent `references/data-sources.md` (MIT, see NOTICE),
> updated to document StackFund's **completed** connectors.

## Source priority
1. **Official exchange data** (TWSE) — anchor of truth.
2. **Company filings / disclosures** (MOPS / TPEX) — OTC + financials.
3. **Yahoo Finance** — narrative / expectation cross-check.
4. **Fresh news / web** — catalyst context, not truth by default.
5. **Contrarian sentiment** — auxiliary, non-authoritative (L3 crowd side-rail).

## Implemented connectors

### TWSE OpenAPI — `src/stackfund/l1_databook/sources/twse.py`
- Endpoint: `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL`
- Returns every listed security's daily OHLCV; filtered to the ETF by `Code`.
- Fields used: `ClosingPrice`, `OpeningPrice`/`HighestPrice`/`LowestPrice`,
  `TradeVolume`, `Change`, `Date` (ROC, e.g. `1150618` → `2026-06-18`).
- **ETF caveat:** the TWSE valuation feed `BWIBBU_ALL` (P/E, dividend yield, P/B)
  **excludes ETFs** (no `0050` row). So ETF **yield / NAV / tracking error** are
  *not* available from the free TWSE feed — they are carried from the data book's
  fundamentals source (frozen fixture today) and labelled accordingly. A dedicated
  ETF-NAV / distribution connector is the next extension.

### Yahoo Finance — `src/stackfund/l1_databook/sources/yahoo.py`
- Endpoint: `https://query1.finance.yahoo.com/v8/finance/chart/<symbol>.TW`
- Unauthenticated. Two uses:
  - `range=5d` `meta` block (`regularMarketPrice`, `chartPreviousClose`,
    `currency`) — **price cross-check** on the TWSE close.
  - `range=1mo` daily **close series** → live **`price_5d_return`** (and a 20-day
    moving average) computed in Python.

### Chips (institutional / margin) — `src/stackfund/l1_databook/sources/chips.py`
- `fetch_institutional_netbuy(symbol)` — TWSE **T86** (three institutional
  investors' daily net buy/sell, 三大法人), via the rwd/zh endpoint.
- `fetch_margin(symbol)` — TWSE **MI_MARGN** (margin financing / short balance).
- Cached ~1h on disk; **graceful** (returns `None` on any failure). Surface via
  `python -m stackfund signals --symbol 0050` (or `scripts/signals.py`).
- **Context only** — chips never enter the DataBook or the decision path.

### News — `src/stackfund/l1_databook/sources/news.py`
- Google News RSS (`hl=zh-TW`), top-N headlines per symbol; stdlib XML; graceful
  (`[]` on failure). Catalyst **context**, never a decision input.

### Trading calendar — `src/stackfund/l1_databook/trading_calendar.py`
- Taipei trading-day calendar (fixed UTC+8): `is_trading_day`,
  `previous_trading_day`, `resolve_report_trading_day`, `trading_session_phase`;
  TWSE holiday API cached at `.hermes-data/tw_market_holidays.json`
  (env: `STACKFUND_HOLIDAY_CACHE_PATH`, `STACKFUND_EXTRA_HOLIDAYS`).

## What is live vs reference (with `--live`)
- **Live:** `price`, `volume_shares` (TWSE STOCK_DAY_ALL) + `price_5d_return`
  (Yahoo series). These are the decision-driving signals.
- **Reference:** `yield`, `nav`, `discount_premium`, `tracking_error`,
  `catalyst_strength` — supplied by a **pluggable `FundamentalsProvider`**
  (`src/stackfund/l1_databook/fundamentals.py`). Default = the fixture, labelled
  reference. `stackfund fetch` prints the live-vs-reference split explicitly.

### Why ETF fundamentals are not live (verified 2026-06)
There is no clean free JSON feed for TW ETF NAV / yield:
- TWSE OpenAPI `BWIBBU_ALL` (P/E·yield·P/B) **excludes ETFs**.
- Yahoo v7/v10 (navPrice / trailingAnnualDividendYield) require a cookie+crumb,
  currently region-gated (401 / Invalid Crumb).
- SITCA (`IN2422`) serves an ASP.NET `__VIEWSTATE` form (POST + HTML scrape).

So fundamentals are a **documented seam**: implement `FundamentalsProvider`
against a stable feed and pass it to `load_databook(..., fundamentals=...)` — the
`SitcaFundamentals` stub shows where. A real provider's values mark the book live.

### Mid-session fallback (from upstream)
When live intraday is limited, use TWSE daily proxies and state the limitation:
`fmtqik` (Highlights of Daily Trading) and `mi-stock20` (Top 20 by Volume), then
Yahoo for narrative context.

## Multi-market seam (roadmap — TW/US equities)

What is market-scoped today, and what generalises:
- **TW-specific:** the TWSE connectors (STOCK_DAY_ALL / T86 / MI_MARGN), the ROC
  date format, the Taipei calendar, the `.TW` Yahoo suffix, NT$-denominated costs.
- **Already general:** the Yahoo chart connector (drop the `.TW` suffix for US
  tickers), the `DataBook`/fixture shape, the pluggable `FundamentalsProvider`
  seam, the HTTP disk cache, freshness labelling.
- **Adding US equities** = a US source module (Yahoo works unauthenticated;
  fundamentals via a provider — e.g. SEC EDGAR facts), a US trading calendar,
  and an equity-flavoured eligibility gate — behind the *same* contracts.
  Per-market source priority stays the same idea: official exchange/filings
  first, Yahoo as cross-check, news as context.

## Freshness & honesty rules
- `freshness=live` means **price/volume** are live (TWSE); fundamentals may still
  be frozen — say so.
- `freshness=frozen` means the whole DataBook is from a fixture.
- Never treat sentiment as truth. If a source is incomplete, mark it, don't invent.
- Each `DataBook` is immutable and hashed (`book_hash`) for replay.
