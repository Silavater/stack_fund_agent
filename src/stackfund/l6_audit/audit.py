"""L6: Audit & Operational P&L — full provenance, replayable.

Decision provenance (pure hard data) and crowd-report provenance (narrative
audit only, non-authoritative) are recorded *separately* and never joined.
"""

from __future__ import annotations

import hashlib

from stackfund.contracts.contrarian_signal import ContrarianSignal
from stackfund.contracts.provenance import CrowdReportProvenance, DecisionProvenance
from stackfund.contracts.rebalance_plan import RebalancePlan


def decision_provenance(plan: RebalancePlan) -> list[DecisionProvenance]:
    rows: list[DecisionProvenance] = []
    for i, d in enumerate(plan.deltas):
        rows.append(
            DecisionProvenance(
                decision_id=f"{plan.plan_id}_{i}",
                scorecard_id=plan.scorecard_id,
                etf_symbol=d.etf_symbol,
                hard_delta_pp=d.hard_delta_pp,
                hard_signals=tuple((r, 0.0) for r in d.hard_reasons),
                final_delta_pp=d.hard_delta_pp,  # == hard_delta_pp, by construction
                action=plan.action,
            )
        )
    if not plan.deltas:
        rows.append(
            DecisionProvenance(
                decision_id=f"{plan.plan_id}_0",
                scorecard_id=plan.scorecard_id,
                etf_symbol="-",
                hard_delta_pp=0.0,
                final_delta_pp=0.0,
                action=plan.action,
            )
        )
    return rows


def crowd_report_provenance(signal: ContrarianSignal) -> CrowdReportProvenance:
    digest = hashlib.sha256(signal.narrative_md.encode("utf-8")).hexdigest()
    return CrowdReportProvenance(
        report_id=f"crp_{signal.seed_id}",
        seed_id=signal.seed_id,
        rng_seed=signal.rng_seed,
        contrarian_modifier=signal.contrarian_modifier,
        narrative_digest=digest,
        is_authoritative=False,
    )
