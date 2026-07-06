"""Read-side firewall contract: the only thing L3 (crowd) is allowed to read.

A ``ScenarioSeed`` is a frozen projection of a DataBook carrying ONLY bucketed
ordinal context (e.g. discount_premium -> "deep_discount"). Personas never see
raw numbers, which structurally prevents the LLM from echoing or recomputing
authoritative figures. The seed is frozen and exposes no setters.
"""

from __future__ import annotations

from dataclasses import dataclass, field

HORIZONS = ("intraday", "swing", "long")
INTENSITIES = ("mild", "severe")


@dataclass(frozen=True)
class ScenarioSeed:
    seed_id: str
    databook_id: str
    rng_seed: int
    market_scenario_label: str
    # Ordinal buckets only — NO raw price/nav/yield numbers.
    ordinal_context: dict[str, str] = field(default_factory=dict)
    seed_hash: str = ""
    # Rehearsal dimensions: which time-scale and how strong the shock. Categorical
    # only (no numeric scalar), so they stay firewall-safe while changing which
    # cohort leads the reaction chain.
    horizon: str = "swing"  # intraday | swing | long
    intensity: str = "mild"  # mild | severe

    def __post_init__(self) -> None:
        assert self.horizon in HORIZONS, "horizon out of vocabulary"
        assert self.intensity in INTENSITIES, "intensity out of vocabulary"
