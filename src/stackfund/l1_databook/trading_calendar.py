"""Taipei trading-day calendar (L1 freshness helper).

Adapted from ST / Chen YuShen's ``stock_agent.trading_calendar`` (MIT) — see ``NOTICE``.
Rewritten to StackFund's package/imports and ``STACKFUND_*`` env names; the logic is
unchanged. Holiday data comes from the TWSE official holiday API with a local JSON cache
(so frozen runs stay fully offline); an env override covers ad-hoc closures (typhoon
days), and a weekday-only fallback keeps it usable when API + cache both miss.

This is a *freshness* helper — "what is the latest trading day / is the market open" —
not a decision input. The deterministic frozen pipeline never calls the network here.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import date, datetime, timedelta, timezone
from datetime import time as dtime
from pathlib import Path
from typing import Any

from stackfund.l1_databook.sources._http import FetchError, fetch_json
from stackfund.l1_databook.sources.twse import twse_date_to_iso

# Taipei is a fixed UTC+8 (Taiwan observes no DST) — a plain offset avoids needing the
# IANA tz database (zoneinfo), which Windows Python ships without.
TAIPEI = timezone(timedelta(hours=8))

TWSE_HOLIDAY_API_URL = "https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule"
DEFAULT_HOLIDAY_CACHE_PATH = ".hermes-data/tw_market_holidays.json"
HOLIDAY_CACHE_MAX_AGE_DAYS = 30

# 09:00-13:30 regular continuous + close-auction session.
SESSION_OPEN = dtime(9, 0)
SESSION_CLOSE = dtime(13, 30)
CLOSE_AUCTION_START = dtime(13, 25)

_CACHE_LOCK = threading.Lock()
_holiday_cache: dict[str, str] | None = None
_holiday_cache_loaded_path: str | None = None


def taipei_now() -> datetime:
    return datetime.now(TAIPEI)


def taipei_today() -> str:
    return taipei_now().date().isoformat()


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5


def _coerce_date(d: date | None) -> date:
    if d is None:
        return taipei_now().date()
    if isinstance(d, datetime):
        return d.date()
    return d


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _holiday_cache_path() -> Path:
    override = os.environ.get("STACKFUND_HOLIDAY_CACHE_PATH", "").strip()
    raw = override or DEFAULT_HOLIDAY_CACHE_PATH
    path = Path(raw)
    if not path.is_absolute():
        path = _repo_root() / path
    return path


def env_extra_holidays() -> set[str]:
    raw = os.environ.get("STACKFUND_EXTRA_HOLIDAYS", "")
    return {token.strip() for token in raw.split(",") if token.strip()}


def parse_twse_holiday_payload(payload: Any) -> set[str]:
    """Map the TWSE holiday-schedule payload to a set of ISO closed-day dates.

    The feed mixes real closures with "resumption" markers (e.g. "國曆新年開始交易日"),
    which are trading days, so those are filtered out.
    """
    holidays: set[str] = set()
    if not isinstance(payload, list):
        return holidays
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("Name") or "")
        description = str(entry.get("Description") or "")
        if "開始交易" in name or "開始交易" in description:
            continue
        iso = twse_date_to_iso(entry.get("Date"))
        if iso and len(iso) == 10 and iso[4] == "-":
            holidays.add(iso)
    return holidays


def _read_holiday_cache_file(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_holiday_cache_file(path: Path, dates: set[str]) -> None:
    record = {"fetched_at": taipei_now().isoformat(timespec="seconds"), "dates": sorted(dates)}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    except OSError:
        return


def _cache_is_stale(record: dict[str, Any]) -> bool:
    fetched_at = record.get("fetched_at")
    if not isinstance(fetched_at, str):
        return True
    try:
        fetched = datetime.fromisoformat(fetched_at)
    except ValueError:
        return True
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=TAIPEI)
    return (taipei_now() - fetched) > timedelta(days=HOLIDAY_CACHE_MAX_AGE_DAYS)


def _load_holiday_cache() -> dict[str, str]:
    """Return {iso_date: 'twse_api'} from the on-disk cache, empty if missing."""
    global _holiday_cache, _holiday_cache_loaded_path
    path = _holiday_cache_path()
    with _CACHE_LOCK:
        if _holiday_cache is not None and _holiday_cache_loaded_path == str(path):
            return dict(_holiday_cache)
        record = _read_holiday_cache_file(path)
        dates = record.get("dates") if isinstance(record, dict) else None
        cache = {str(d): "twse_api" for d in dates} if isinstance(dates, list) else {}
        _holiday_cache = cache
        _holiday_cache_loaded_path = str(path)
        return dict(cache)


def refresh_holiday_cache(*, force: bool = False) -> dict[str, Any]:
    """Fetch the TWSE holiday list and persist it. Never raises; keeps the cache on failure."""
    global _holiday_cache, _holiday_cache_loaded_path
    path = _holiday_cache_path()
    if not force:
        record = _read_holiday_cache_file(path)
        if isinstance(record, dict) and record.get("dates") and not _cache_is_stale(record):
            return {"status": "fresh", "source": "twse_api", "count": len(record["dates"])}
    try:
        payload = fetch_json(TWSE_HOLIDAY_API_URL)
    except FetchError:
        return {"status": "error", "source": "weekday_only", "count": 0}
    dates = parse_twse_holiday_payload(payload)
    _write_holiday_cache_file(path, dates)
    with _CACHE_LOCK:
        _holiday_cache = {d: "twse_api" for d in dates}
        _holiday_cache_loaded_path = str(path)
    return {"status": "refreshed", "source": "twse_api", "count": len(dates)}


def calendar_source(d: date | None = None) -> str:
    """'twse_api' when holiday data exists for the year, else 'weekday_only'."""
    d = _coerce_date(d)
    cache = _load_holiday_cache()
    if not cache:
        return "weekday_only"
    if any(iso.startswith(f"{d.year:04d}-") for iso in cache):
        return "twse_api"
    return "weekday_only"


def is_taiwan_holiday(d: date | None = None) -> bool:
    d = _coerce_date(d)
    iso = d.isoformat()
    if iso in env_extra_holidays():
        return True
    return iso in _load_holiday_cache()


def is_trading_day(d: date | None = None) -> bool:
    d = _coerce_date(d)
    if is_weekend(d):
        return False
    return not is_taiwan_holiday(d)


def previous_trading_day(d: date | None = None) -> date:
    d = _coerce_date(d)
    cursor = d - timedelta(days=1)
    for _ in range(30):
        if is_trading_day(cursor):
            return cursor
        cursor -= timedelta(days=1)
    return cursor


def resolve_report_trading_day(d: date | None = None) -> date:
    """The trading day a report belongs to: today if trading, else the previous one."""
    d = _coerce_date(d)
    return d if is_trading_day(d) else previous_trading_day(d)


def in_trading_session(now: datetime | None = None) -> bool:
    now = now or taipei_now()
    if not is_trading_day(now.date()):
        return False
    return SESSION_OPEN <= now.time() <= SESSION_CLOSE


def trading_session_phase(now: datetime | None = None) -> str:
    now = now or taipei_now()
    if not is_trading_day(now.date()):
        return "closed_day"
    current = now.time()
    if current < SESSION_OPEN:
        return "pre_open"
    if current >= SESSION_CLOSE:
        return "after_close"
    if current >= CLOSE_AUCTION_START:
        return "close_auction"
    return "open"


def _reset_cache_for_tests() -> None:
    global _holiday_cache, _holiday_cache_loaded_path
    with _CACHE_LOCK:
        _holiday_cache = None
        _holiday_cache_loaded_path = None
