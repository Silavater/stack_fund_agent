"""L1: deterministic ingest -> immutable DataBook (computes every number).

Frozen fixtures are the default (deterministic core, zero egress). ``load_databook``
can OPT IN to a live overlay: official TWSE price/volume + a Yahoo-derived
``price_5d_return``. ETF fundamentals (yield / NAV / discount_premium /
tracking_error) come from a pluggable ``FundamentalsProvider`` — default is the
fixture (labelled *reference*); pass a real provider to make them live.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from stackfund.contracts.databook import DataBook
from stackfund.l1_databook.fundamentals import FixtureFundamentals, FundamentalsProvider

# Fields that become live via the network connectors (not fundamentals).
LIVE_PRICE_FIELDS = ("price", "volume_shares")  # TWSE STOCK_DAY_ALL
LIVE_MOMENTUM_FIELDS = ("price_5d_return",)  # Yahoo chart series


def _hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def build_databook(
    symbol: str,
    metrics: dict[str, float],
    observed_at: str,
    freshness: str = "frozen",
    price_series: tuple[float, ...] = (),
) -> DataBook:
    series = tuple(float(x) for x in price_series)
    book_hash = _hash(
        {
            "symbol": symbol,
            "metrics": metrics,
            "observed_at": observed_at,
            "price_series": list(series),
        }
    )
    return DataBook(
        book_id=f"db_{symbol}_{book_hash[:8]}",
        etf_symbol=symbol,
        observed_at=observed_at,
        freshness=freshness,
        metrics=dict(metrics),
        book_hash=book_hash,
        price_series=series,
    )


def load_databook_from_fixture(path: str | Path) -> DataBook:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return build_databook(
        symbol=data["symbol"],
        metrics=data["metrics"],
        observed_at=data["observed_at"],
        freshness=data.get("freshness", "frozen"),
        price_series=tuple(data.get("price_series", ())),
    )


def _default_fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "fixtures"


def _safe(fn: Callable[[], Any]) -> Any:
    """Run a network call; return None on any failure (graceful fallback)."""
    try:
        return fn()
    except Exception:
        return None


def load_databook(
    symbol: str,
    live: bool = False,
    fixtures_dir: str | Path | None = None,
    fundamentals: FundamentalsProvider | None = None,
) -> DataBook:
    """Build a DataBook for ``symbol``.

    * ``live=True`` overlays official TWSE daily price/volume + a Yahoo-derived
      5-day return (freshness=live).
    * ``fundamentals`` is a pluggable provider for yield/NAV/etc.; default is the
      fixture (reference). A real provider applying live fundamentals also marks
      the book live.
    """
    base = Path(fixtures_dir) if fixtures_dir else _default_fixtures_dir()
    data = json.loads((base / f"etf_{symbol}.json").read_text(encoding="utf-8"))
    fixture_metrics = dict(data["metrics"])
    observed_at = data["observed_at"]
    freshness = data.get("freshness", "frozen")
    metrics = dict(fixture_metrics)
    price_series = tuple(data.get("price_series", ()))

    provider = fundamentals or FixtureFundamentals(fixture_metrics)
    supplied = provider.fundamentals(symbol)
    if supplied:
        metrics.update(supplied)
        if provider.name != "fixture":
            freshness = "live"  # a real fundamentals feed was applied

    if live:
        from stackfund.l1_databook.sources import twse, yahoo

        quote = _safe(lambda: twse.fetch_etf_quote(symbol))
        if quote and quote.get("close") is not None:
            metrics["price"] = quote["close"]
            if quote.get("volume_shares") is not None:
                metrics["volume_shares"] = quote["volume_shares"]
            observed_at = quote.get("observed_at") or observed_at
            freshness = "live"

        hist = _safe(lambda: yahoo.fetch_yahoo_history(symbol))
        if hist and hist.get("price_5d_return_pct") is not None:
            metrics["price_5d_return"] = hist["price_5d_return_pct"]
            freshness = "live"

    return build_databook(symbol, metrics, observed_at, freshness, price_series)
