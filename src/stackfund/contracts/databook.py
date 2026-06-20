"""L1 output contract: the immutable ETF data book (authoritative numbers)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DataBook:
    """Immutable snapshot of one ETF's deterministic metrics.

    ``metrics`` holds the authoritative numbers computed by L1 (price, nav,
    discount_premium, tracking_error, yield, ...). This is the ONLY place raw
    numbers live; the crowd side-rail (L3) never receives this object — it only
    sees a bucketed, frozen ``ScenarioSeed`` projection.
    """

    book_id: str
    etf_symbol: str
    observed_at: str
    freshness: str  # "frozen" | "live" | "partial"
    metrics: dict[str, float] = field(default_factory=dict)
    book_hash: str = ""
