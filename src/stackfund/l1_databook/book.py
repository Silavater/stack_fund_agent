"""L1: deterministic ingest -> immutable DataBook (computes every number).

Frozen fixtures are the default (deterministic core, zero egress). ``load_databook``
can OPT IN to a live TWSE price/volume overlay; ETF fundamentals (yield / NAV /
tracking error) are carried from the fixture because the free TWSE valuation feed
excludes ETFs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stackfund.contracts.databook import DataBook


def _hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def build_databook(
    symbol: str,
    metrics: dict[str, float],
    observed_at: str,
    freshness: str = "frozen",
) -> DataBook:
    book_hash = _hash({"symbol": symbol, "metrics": metrics, "observed_at": observed_at})
    return DataBook(
        book_id=f"db_{symbol}_{book_hash[:8]}",
        etf_symbol=symbol,
        observed_at=observed_at,
        freshness=freshness,
        metrics=dict(metrics),
        book_hash=book_hash,
    )


def load_databook_from_fixture(path: str | Path) -> DataBook:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return build_databook(
        symbol=data["symbol"],
        metrics=data["metrics"],
        observed_at=data["observed_at"],
        freshness=data.get("freshness", "frozen"),
    )


def _default_fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "fixtures"


def _try_live_quote(symbol: str) -> dict | None:
    """Best-effort live TWSE quote; returns None on any network/parse failure."""
    try:
        from stackfund.l1_databook.sources import twse

        return twse.fetch_etf_quote(symbol)
    except Exception:
        return None


def load_databook(
    symbol: str, live: bool = False, fixtures_dir: str | Path | None = None
) -> DataBook:
    """Build a DataBook for ``symbol``. With ``live=True``, overlay the official
    TWSE daily price/volume on top of the fixture fundamentals (freshness=live);
    otherwise return the frozen fixture unchanged."""
    base = Path(fixtures_dir) if fixtures_dir else _default_fixtures_dir()
    data = json.loads((base / f"etf_{symbol}.json").read_text(encoding="utf-8"))
    metrics = dict(data["metrics"])
    observed_at = data["observed_at"]
    freshness = data.get("freshness", "frozen")

    if live:
        quote = _try_live_quote(symbol)
        if quote and quote.get("close") is not None:
            metrics["price"] = quote["close"]
            if quote.get("volume_shares") is not None:
                metrics["volume_shares"] = quote["volume_shares"]
            observed_at = quote.get("observed_at") or observed_at
            freshness = "live"  # price/volume live; fundamentals carried from fixture

    return build_databook(symbol, metrics, observed_at, freshness)
