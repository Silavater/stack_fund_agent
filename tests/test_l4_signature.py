"""L4 entrypoint signature guard: build_rebalance_plan accepts ONLY a ScoreCard.

Encodes the doc's invariant "L4 輸入型別只有 ScoreCard" — the crowd modifier can
never enter the decision because there is no parameter for it.
"""

from __future__ import annotations

import inspect

from stackfund.l4_portfolio.plan import build_rebalance_plan


def test_l4_entrypoint_takes_only_scorecard():
    params = inspect.signature(build_rebalance_plan).parameters
    assert list(params) == ["scorecard"], f"unexpected params: {list(params)}"
    annotation = str(params["scorecard"].annotation)
    assert "ContrarianSignal" not in annotation, f"L4 must not accept crowd signal: {annotation}"
    assert "ScoreCard" in annotation, f"L4 must be typed ScoreCard: {annotation}"
