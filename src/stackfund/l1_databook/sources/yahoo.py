"""Yahoo Finance connector — unauthenticated v8 chart API.

Completes ``scripts/fetch_yahoo.py`` from AZNitro/tw-stock-agent. The chart
endpoint needs no auth/crumb. Two uses:
  * ``fetch_yahoo_quote``   — quote meta (price cross-check on the TWSE close)
  * ``fetch_yahoo_history`` — daily close series -> live ``price_5d_return`` + MA20
"""

from __future__ import annotations

from typing import Any

from stackfund.l1_databook.sources._http import get_json

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.TW?range={range}&interval={interval}"
_TIMEOUT = 15


def parse_chart(payload: dict, symbol: str) -> dict[str, Any] | None:
    """Extract the quote meta from a Yahoo chart payload. Pure (no network)."""
    try:
        meta = payload["chart"]["result"][0]["meta"]
    except (KeyError, IndexError, TypeError):
        return None
    return {
        "symbol": symbol,
        "price": meta.get("regularMarketPrice"),
        "previous_close": meta.get("chartPreviousClose"),
        "currency": meta.get("currency"),
        "source": "Yahoo:chart",
    }


def parse_chart_series(payload: dict, symbol: str) -> dict[str, Any] | None:
    """Extract the daily close series + derived signals. Pure (no network)."""
    try:
        result = payload["chart"]["result"][0]
        meta = result["meta"]
        raw = result["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError, TypeError):
        return None
    closes = [c for c in raw if c is not None]
    if not closes:
        return None
    out: dict[str, Any] = {
        "symbol": symbol,
        "price": meta.get("regularMarketPrice") or closes[-1],
        "previous_close": meta.get("chartPreviousClose"),
        "currency": meta.get("currency"),
        "n_closes": len(closes),
        "closes": closes,  # the daily close series itself (for charting)
        "price_5d_return_pct": None,
        "ma20": None,
        "source": "Yahoo:chart-series",
    }
    if len(closes) >= 6:
        out["price_5d_return_pct"] = round((closes[-1] / closes[-6] - 1) * 100, 3)
    if len(closes) >= 20:
        out["ma20"] = round(sum(closes[-20:]) / 20.0, 3)
    return out


def fetch_yahoo_quote(symbol: str, timeout: int = _TIMEOUT) -> dict | None:
    url = CHART_URL.format(symbol=symbol, range="5d", interval="1d")
    return parse_chart(get_json(url, {"User-Agent": "Mozilla/5.0"}, timeout), symbol)


def fetch_yahoo_history(
    symbol: str, range_: str = "1mo", interval: str = "1d", timeout: int = _TIMEOUT
) -> dict | None:
    url = CHART_URL.format(symbol=symbol, range=range_, interval=interval)
    return parse_chart_series(get_json(url, {"User-Agent": "Mozilla/5.0"}, timeout), symbol)
