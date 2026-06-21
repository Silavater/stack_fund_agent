"""Three separate ledgers — never conflated.

* PortfolioLedger  — SIMULATED ETF allocation (research illustration, NOT orders)
* FinOpsLedger     — Stripe revenue + SaaS/API expenses (the business, not ETFs)
* ExperimentLedger — run metadata (seed, versions) for replay

Critical honesty rule: a Stripe test charge is FinOps, never "ETF investment
P&L". The product places no securities orders; the portfolio ledger is an
illustrative "if you followed this allocation" view only.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from stackfund.contracts.finops import OperationalPnL, OperationalReceipt
from stackfund.contracts.rebalance_plan import RebalancePlan


@dataclass(frozen=True)
class PortfolioLedgerEntry:
    run_id: str
    etf_symbol: str
    action: str
    simulated_delta_pp: float
    simulated: bool = True  # research illustration — NOT an order/fill


@dataclass(frozen=True)
class FinOpsLedger:
    run_id: str
    receipts: tuple[OperationalReceipt, ...]
    pnl: OperationalPnL


@dataclass(frozen=True)
class ExperimentLedger:
    run_id: str
    parent_run_id: str
    rng_seed: int
    scenario_label: str
    formula_version: str = "etf-score-v1.2.0"
    code_commit: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)


def portfolio_ledger(
    run_id: str, plans: Iterable[RebalancePlan]
) -> tuple[PortfolioLedgerEntry, ...]:
    out: list[PortfolioLedgerEntry] = []
    for plan in plans:
        if plan.deltas:
            for d in plan.deltas:
                out.append(PortfolioLedgerEntry(run_id, d.etf_symbol, plan.action, d.hard_delta_pp))
        else:
            out.append(PortfolioLedgerEntry(run_id, "-", plan.action, 0.0))
    return tuple(out)


def finops_ledger(
    run_id: str, receipts: Iterable[OperationalReceipt], pnl: OperationalPnL
) -> FinOpsLedger:
    return FinOpsLedger(run_id=run_id, receipts=tuple(receipts), pnl=pnl)


def experiment_ledger(
    run_id: str, parent_run_id: str, rng_seed: int, scenario_label: str
) -> ExperimentLedger:
    return ExperimentLedger(
        run_id=run_id,
        parent_run_id=parent_run_id,
        rng_seed=rng_seed,
        scenario_label=scenario_label,
        notes=("VoI data purchases take effect in the NEXT run (immutable inputs per run).",),
    )
