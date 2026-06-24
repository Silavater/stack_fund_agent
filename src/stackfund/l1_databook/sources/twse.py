"""TWSE OpenAPI connector — official ETF daily price/volume (STOCK_DAY_ALL).

Completes ``scripts/fetch_twse.py`` from AZNitro/tw-stock-agent (which only built
a URL). The official endpoint returns every listed security's daily OHLCV; we
filter to the requested ETF. Note: ETF dividend yield / NAV are NOT in the free
TWSE valuation feed (BWIBBU_ALL excludes ETFs), so those fundamentals are carried
from the data book's fundamentals source, not this connector.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from stackfund.l1_databook.sources._http import get_json

STOCK_DAY_ALL_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
_TIMEOUT = 15


def roc_date_to_iso(roc: str) -> str:
    """Convert a TWSE ROC date (e.g. ``1150618``) to ISO ``2026-06-18``."""
    roc = (roc or "").strip()
    if len(roc) < 5:
        return ""
    year = int(roc[:-4]) + 1911
    return f"{year:04d}-{roc[-4:-2]}-{roc[-2:]}"


def _to_float(value: Any) -> float | None:
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None


def twse_date_to_iso(value: Any) -> str | None:
    """Map a TWSE date — 7-digit ROC (``1150618``) or 8-digit Gregorian (``20260618``) —
    to ISO. The holiday-schedule feed uses Gregorian, so ``roc_date_to_iso`` alone won't
    do. Adapted from ST / Chen YuShen's ``stock_agent.utils`` (MIT) — see ``NOTICE``.
    """
    if value is None:
        return None
    text = str(value).strip().replace("/", "").replace("-", "")
    if not text:
        return None
    try:
        if len(text) == 7:
            year, month, day = int(text[:3]) + 1911, int(text[3:5]), int(text[5:7])
        elif len(text) == 8:
            year, month, day = int(text[:4]), int(text[4:6]), int(text[6:8])
        else:
            return str(value)
    except ValueError:
        return str(value)
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_float(value: Any) -> float | None:
    """Robust float parse (strips commas / ``N/A`` markers / leading non-numerics).
    Adapted from ST / Chen YuShen's ``stock_agent.utils`` (MIT) — see ``NOTICE``.
    """
    import re

    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text in {"-", "--", "N/A", "NaN"}:
        return None
    text = re.sub(r"^[^\d+\-.]+", "", text)
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def parse_stock_day_all(rows: list[dict], symbol: str) -> dict[str, Any] | None:
    """Extract one ETF's quote from a STOCK_DAY_ALL payload. Pure (no network)."""
    for row in rows:
        if row.get("Code") == symbol:
            return {
                "symbol": symbol,
                "name": row.get("Name", ""),
                "observed_at": roc_date_to_iso(row.get("Date", "")),
                "close": _to_float(row.get("ClosingPrice")),
                "open": _to_float(row.get("OpeningPrice")),
                "high": _to_float(row.get("HighestPrice")),
                "low": _to_float(row.get("LowestPrice")),
                "change": _to_float(row.get("Change")),
                "volume_shares": _to_float(row.get("TradeVolume")),
                "source": "TWSE:STOCK_DAY_ALL",
            }
    return None


@lru_cache(maxsize=4)
def fetch_stock_day_all(url: str = STOCK_DAY_ALL_URL, timeout: int = _TIMEOUT) -> list[dict]:
    """Fetch the full daily payload (cached per-process to amortise the ~300KB pull)."""
    return get_json(url, {"User-Agent": "StackFund/0.1"}, timeout)


def fetch_etf_quote(symbol: str, timeout: int = _TIMEOUT) -> dict | None:
    return parse_stock_day_all(fetch_stock_day_all(timeout=timeout), symbol)
