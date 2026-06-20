# Data sources (priority order)

1. **TWSE OpenAPI** (authoritative): price/volume, margin balance, P/E, P/B,
   yield, announcements. https://openapi.twse.com.tw/
2. **TPEX / MOPS**: OTC + financials/dividends. https://mops.twse.com.tw/
3. **Yahoo Finance**: quotes, analyst targets, peers, news.
4. **Web / News**: catalyst events.
5. **Contrarian sentiment** (auxiliary layer only): overheating / panic / crowding.

ETF-specific fields (discount/premium, tracking error, constituent overlap,
ex-dividend date) are **always computed deterministically in Python** (L1), never
inferred by the model.

Freshness is tagged on every DataBook (`frozen` / `live` / `partial`). Missing
data is marked `partial` — never fabricated.

> MVP note: fixtures under `fixtures/etf_*.json` are frozen samples. Live
> fetchers (TWSE price/volume + Yahoo quote) are the first connectors to add.
