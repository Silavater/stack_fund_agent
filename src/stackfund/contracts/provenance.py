"""L6 contracts: separated decision vs. crowd-report provenance.

Decision provenance is pure hard data. Crowd-report provenance is recorded for
narrative audit only and is flagged non-authoritative; the two are never joined
on a decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DecisionProvenance:
    decision_id: str
    scorecard_id: str
    etf_symbol: str
    hard_delta_pp: float
    hard_signals: tuple[tuple[str, float], ...] = field(default_factory=tuple)
    final_delta_pp: float = 0.0  # == hard_delta_pp, by construction
    action: str = ""
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    authoritative_input_hash: str = ""


@dataclass(frozen=True)
class CrowdReportProvenance:
    report_id: str
    seed_id: str
    rng_seed: int
    crowd_consensus: str
    engine_posture: str
    divergence_bucket: str
    narrative_digest: str  # sha256 of the narrative
    non_authoritative: bool = True  # always True; for narrative audit only
