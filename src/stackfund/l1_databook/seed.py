"""L1: project a DataBook into a frozen, bucketed ScenarioSeed for L3.

Raw numbers are dropped here — only ordinal buckets cross the firewall, so the
crowd personas can never see or echo an authoritative figure.
"""

from __future__ import annotations

import hashlib
import json

from stackfund.contracts.databook import DataBook
from stackfund.contracts.scenario_seed import ScenarioSeed


def _bucket_discount_premium(x: float) -> str:
    if x <= -1.0:
        return "deep_discount"
    if x < -0.1:
        return "discount"
    if x <= 0.1:
        return "fair"
    if x < 1.0:
        return "premium"
    return "rich"


def _bucket_yield(x: float) -> str:
    if x < 3.0:
        return "low"
    if x <= 6.0:
        return "normal"
    return "high"


def make_seed(book: DataBook, market_scenario_label: str, rng_seed: int = 42) -> ScenarioSeed:
    ordinal = {
        "discount_premium": _bucket_discount_premium(book.metrics.get("discount_premium", 0.0)),
        "yield": _bucket_yield(book.metrics.get("yield", 0.0)),
    }
    seed_hash = hashlib.sha256(
        json.dumps(
            {
                "book": book.book_hash,
                "label": market_scenario_label,
                "rng": rng_seed,
                "ordinal": ordinal,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:16]
    return ScenarioSeed(
        seed_id=f"seed_{book.etf_symbol}_{seed_hash[:8]}",
        databook_id=book.book_id,
        rng_seed=rng_seed,
        market_scenario_label=market_scenario_label,
        ordinal_context=ordinal,
        seed_hash=seed_hash,
    )
