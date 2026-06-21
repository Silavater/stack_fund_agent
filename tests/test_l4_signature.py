"""L4 entrypoint signature guard: build_rebalance_plan accepts ONLY AuthoritativeState.

Encodes the doc's invariant "L4 reads only AuthoritativeState; never a FACE
artifact" — the crowd side can never enter the decision because there is no
parameter for it.
"""

from __future__ import annotations

import inspect

from stackfund.l4_portfolio.plan import build_rebalance_plan


def test_l4_entrypoint_takes_only_authoritative_state():
    params = inspect.signature(build_rebalance_plan).parameters
    assert list(params) == ["state"], f"unexpected params: {list(params)}"
    annotation = str(params["state"].annotation)
    for forbidden in ("CrowdNarrative", "NarrativeDivergence", "crowd", "divergence"):
        assert forbidden.lower() not in annotation.lower(), f"L4 must not accept FACE: {annotation}"
    assert "AuthoritativeState" in annotation, (
        f"L4 must be typed AuthoritativeState; got {annotation}"
    )
