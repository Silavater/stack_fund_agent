"""Read-side firewall contract: the only thing L3 (crowd) is allowed to read.

A ``ScenarioSeed`` is a frozen projection of a DataBook carrying ONLY bucketed
ordinal context (e.g. discount_premium -> "deep_discount"). Personas never see
raw numbers, which structurally prevents the LLM from echoing or recomputing
authoritative figures. The seed is frozen and exposes no setters.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScenarioSeed:
    seed_id: str
    databook_id: str
    rng_seed: int
    market_scenario_label: str
    # Ordinal buckets only — NO raw price/nav/yield numbers.
    ordinal_context: dict[str, str] = field(default_factory=dict)
    seed_hash: str = ""
