"""L1: deterministic ingest -> immutable DataBook (computes every number)."""

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
