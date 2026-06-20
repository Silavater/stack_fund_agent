"""L5 contracts: operational receipts and the single Operational P&L."""

from __future__ import annotations

from dataclasses import dataclass

# Receipt types the demo must be able to represent.
SPEND = "spend"
EARN = "earn"
REFUSED_SPEND = "refused_spend"
BLOCKED = "blocked"
MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True)
class OperationalReceipt:
    receipt_id: str
    type: str  # one of the constants above
    status: str
    amount: float
    currency: str = "TWD"
    reason: str | None = None


@dataclass(frozen=True)
class OperationalPnL:
    period: str
    revenue: float
    cost: float

    @property
    def gross_margin(self) -> float:
        return round(self.revenue - self.cost, 2)
