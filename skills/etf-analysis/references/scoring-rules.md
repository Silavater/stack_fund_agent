# Scoring rules (transparent, hand-auditable — synced to the engine)

> Source of truth: `src/stackfund/l2_scorecard/scorecard.py`,
> `src/stackfund/contracts/scorecard.py`, `src/stackfund/l4_portfolio/plan.py`.
> If this file and the code ever disagree, the code wins — update this file.

## L2 eligibility gate (runs first — fail → `NO_ACTION [INELIGIBLE, …]`)

| check | reason code |
|---|---|
| `freshness ∉ {fresh, frozen, live}` | `STALE_OR_MISSING` |
| `leveraged_or_inverse ≥ 1.0` | `LEVERAGED_OR_INVERSE` |
| `history_days < 60` | `INSUFFICIENT_HISTORY` |
| `avg_volume_lots < 1000` | `VOLUME_TOO_LOW` |
| `nav_comparable < 1.0` | `NAV_NOT_COMPARABLE` |

e.g. `00631L` (2× leveraged) → `NO_ACTION [INELIGIBLE, LEVERAGED_OR_INVERSE]`, by design.

## L2 sub-scores (all clipped to [-1, +1]; risk to [0, 1])

| sub-score      | formula                                                          |
|----------------|------------------------------------------------------------------|
| trend          | `price_5d_return / 5` (short-window, last 5 days)                |
| momentum_slope | OLS slope of `price_series` / mean price × 200, clipped [-1,+1]; `0.0` if series < 5 pts (medium-term, full series) |
| valuation      | `-discount_premium / 2` (a discount is cheaper → +)             |
| fundamental    | `(yield - 4) / 4`                                                |
| catalyst       | `catalyst_strength`                                             |
| risk           | `tracking_error / 2` (clipped 0..1)                            |

## Composite (in `ScoreCard.composite()`)

```
composite = 0.20*trend + 0.10*momentum_slope + 0.25*valuation
          + 0.20*fundamental + 0.15*catalyst - 0.10*risk
```

> `trend` and `momentum_slope` split the old 0.30 trend weight (0.20 + 0.10) so the
> medium-term full-series trend gets a voice alongside the short 5-day window — a
> series can be up over 24 days while down over 5 (e.g. 0056). Weights still total
> 0.90 positive − 0.10 risk, matching the pre-momentum mix.

## L4 decision (in `build_rebalance_plan`; policy defaults in `contracts/policy.py`)

```
target_weight = 1/n_holdings + composite * (base_weight_tilt_pp / 100)   # tilt_pp = 15
                (capped at max_weight_per_etf = 0.40)
raw_delta_pp  = (target_weight - current_weight) * 100
benefit_bps   = |composite| * ALPHA_BPS            # ALPHA_BPS = 300
cost_bps      = CostModel.round_trip_bps           # 19bps default
```

Gates, in order (each → a first-class `NO_ACTION` with its reason code):
1. `|raw_delta_pp| < tolerance_pp (1.0)` → `WITHIN_TOLERANCE`
2. `benefit_bps < cost_bps` → `EXPECTED_BENEFIT_BELOW_TRANSACTION_COST`

Otherwise → `REBALANCE` with `hard_delta_pp` clamped to
`±max_delta_pp_per_run (5.0pp)` — which is why demo rebalances show `+5.00pp`.

**R5 mitigation:** scores are *derived from observable signals*, not fed in, so
the conclusion cannot be "the input we wanted". Every plan carries an
`authoritative_input_hash` for replay; recompute any number by hand from the
formulas above.

## Multi-market note (roadmap — TW/US equities)

The gate + scorecard fields are **instrument-scoped for ETFs** (tracking error,
NAV comparability, leveraged flag). Extending to individual TW/US equities means
an equity variant of both (e.g. liquidity/free-float gates; PE/PB/ROE-style
fundamental scores) behind the same `DataBook → ScoreCard → plan` contracts —
the L4 math above (tilt, tolerance, benefit-vs-cost, clamp) is already
instrument-agnostic.
