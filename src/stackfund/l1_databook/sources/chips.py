"""Taiwan institutional + margin "chips" connectors (TWSE T86 + MI_MARGN).

Adapted from ST / Chen YuShen's ``stock_agent.providers.twse`` (MIT) — see ``NOTICE``.
Returns plain dicts. Chips are **context, never a decision input**, and both functions
are graceful (return ``None`` on any failure). Responses are cached (~1h) since these
feeds update once per trading day.
"""

from __future__ import annotations

from stackfund.l1_databook.sources._http import FetchError, fetch_json
from stackfund.l1_databook.sources.twse import parse_int, twse_date_to_iso

_T86_URL = "https://www.twse.com.tw/rwd/zh/fund/T86?date={date}&selectType=ALLBUT0999&response=json"
_MI_MARGN_URL = "https://openapi.twse.com.tw/v1/exchangeReport/MI_MARGN"
_TIMEOUT = 15
_CACHE_TTL = 3600.0


def _date_token(date: str | None) -> str:
    if date:
        return date.replace("-", "")
    from stackfund.l1_databook import trading_calendar as tc

    return tc.resolve_report_trading_day().strftime("%Y%m%d")


def fetch_institutional_netbuy(symbol: str, date: str | None = None) -> dict | None:
    """Three-investor net-buy (shares) for one symbol from TWSE T86. ``None`` on failure."""
    url = _T86_URL.format(date=_date_token(date))
    try:
        payload = fetch_json(url, timeout=_TIMEOUT, cache_ttl=_CACHE_TTL)
    except FetchError:
        return None
    if not isinstance(payload, dict):
        return None
    fields = payload.get("fields") or []
    code = symbol.strip().upper()
    for item in payload.get("data") or []:
        if not isinstance(item, list):
            continue
        row = dict(zip(fields, item, strict=False))
        if str(row.get("證券代號", "")).strip().upper() == code:
            return {
                "symbol": symbol,
                "date": twse_date_to_iso(payload.get("date")),
                "foreign_net_buy": parse_int(row.get("外陸資買賣超股數(不含外資自營商)")),
                "trust_net_buy": parse_int(row.get("投信買賣超股數")),
                "dealer_net_buy": parse_int(row.get("自營商買賣超股數")),
                "total_net_buy": parse_int(row.get("三大法人買賣超股數")),
                "source": "TWSE:T86",
            }
    return None


def fetch_margin(symbol: str) -> dict | None:
    """Margin / short balances for one symbol from TWSE MI_MARGN. ``None`` on failure."""
    try:
        rows = fetch_json(_MI_MARGN_URL, timeout=_TIMEOUT, cache_ttl=_CACHE_TTL)
    except FetchError:
        return None
    if not isinstance(rows, list):
        return None
    code = symbol.strip().upper()
    for row in rows:
        if str(row.get("股票代號", "")).strip().upper() == code:
            mt, mp = parse_int(row.get("融資今日餘額")), parse_int(row.get("融資前日餘額"))
            st, sp = parse_int(row.get("融券今日餘額")), parse_int(row.get("融券前日餘額"))
            return {
                "symbol": symbol,
                "margin_balance": mt,
                "margin_change": (mt - mp) if mt is not None and mp is not None else None,
                "short_balance": st,
                "short_change": (st - sp) if st is not None and sp is not None else None,
                "source": "TWSE:MI_MARGN",
            }
    return None
