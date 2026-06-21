"""L5: FinOps — Stripe earn/spend orchestration + deterministic VoI gate.

The crowd modifier never participates in spend decisions (not even as a
tie-breaker); this module does not import the crowd side-rail.
"""

from __future__ import annotations

from collections.abc import Iterable

from stackfund.contracts.finops import (
    EARN,
    REFUSED_SPEND,
    SPEND,
    OperationalPnL,
    OperationalReceipt,
)


def value_of_information_gate(
    materiality: float, cap_headroom: float, threshold: float = 0.3
) -> bool:
    """Decide whether a paid report/provision is worth running. Pure hard data."""
    return materiality >= threshold and cap_headroom > 0.0


def record_earn(receipt_id: str, amount: float, currency: str = "TWD") -> OperationalReceipt:
    return OperationalReceipt(
        receipt_id=receipt_id, type=EARN, status="succeeded", amount=amount, currency=currency
    )


def make_receipt(
    receipt_id: str,
    rtype: str,
    status: str,
    amount: float,
    currency: str = "TWD",
    reason: str | None = None,
) -> OperationalReceipt:
    """Build an OperationalReceipt from a (real Stripe or stub) payment result."""
    return OperationalReceipt(
        receipt_id=receipt_id,
        type=rtype,
        status=status,
        amount=amount,
        currency=currency,
        reason=reason,
    )


def attempt_spend(
    receipt_id: str, amount: float, cap_remaining: float, currency: str = "TWD"
) -> OperationalReceipt:
    """Attempt a spend; refuse (hard) if it would breach the remaining cap."""
    if amount > cap_remaining:
        return OperationalReceipt(
            receipt_id=receipt_id,
            type=REFUSED_SPEND,
            status="refused",
            amount=amount,
            currency=currency,
            reason=f"monthly cap breach: {amount:.0f} > headroom {cap_remaining:.0f}",
        )
    return OperationalReceipt(
        receipt_id=receipt_id, type=SPEND, status="succeeded", amount=amount, currency=currency
    )


def operational_pnl(period: str, receipts: Iterable[OperationalReceipt]) -> OperationalPnL:
    receipts = list(receipts)
    revenue = sum(r.amount for r in receipts if r.type == EARN and r.status == "succeeded")
    cost = sum(r.amount for r in receipts if r.type == SPEND and r.status == "succeeded")
    return OperationalPnL(period=period, revenue=round(revenue, 2), cost=round(cost, 2))
