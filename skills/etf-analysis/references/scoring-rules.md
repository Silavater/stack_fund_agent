# Scoring rules (transparent, hand-auditable)

L2 produces five sub-scores from observable L1 metrics (see
`src/stackfund/l2_scorecard/scorecard.py`). All clipped to [-1, +1]:

| sub-score    | formula (placeholder weights — finalise in Day 3)        |
|--------------|----------------------------------------------------------|
| trend        | `price_5d_return / 5`                                     |
| valuation    | `-discount_premium / 2` (a discount is cheaper → +)      |
| fundamental  | `(yield - 4) / 4`                                         |
| catalyst     | `catalyst_strength`                                      |
| risk         | `tracking_error / 2` (0..1)                               |

Composite (L4 input):
```
composite = 0.30*trend + 0.25*valuation + 0.20*fundamental + 0.15*catalyst - 0.10*risk
hard_delta_pp = composite * 6
```
`|hard_delta_pp| < 1.0pp` → **NO_ACTION**. Otherwise REBALANCE with the listed
hard reasons.

**R5 mitigation:** scores are *derived from observable signals*, not fed in, so
the conclusion cannot be "the input we wanted". Print the seed to hand-recompute.
