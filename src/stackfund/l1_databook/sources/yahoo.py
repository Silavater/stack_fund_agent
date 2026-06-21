"""Yahoo Finance connector — unauthenticated v8 chart API (price cross-check).

Completes ``scripts/fetch_yahoo.py`` from AZNitro/tw-stock-agent (which only built
URLs). The chart endpoint needs no auth/crumb and returns a quote ``meta`` block;
we use it as a narrative-layer cross-check on the official TWSE close.
"""

from __future__ import annotations

from typing import Any

from stackfund.l1_databook.sources._http import get_json

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.TW?range=5d&interval=1d"
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


def fetch_yahoo_quote(symbol: str, timeout: int = _TIMEOUT) -> dict | None:
    payload = get_json(CHART_URL.format(symbol=symbol), {"User-Agent": "Mozilla/5.0"}, timeout)
    return parse_chart(payload, symbol)
