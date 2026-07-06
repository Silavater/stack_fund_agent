# DONE snapshot — part-001-slice-004

Part: part-001
Slice: slice-004
Status: done
Date: 2026-07-06
Design authority: `.beacon/parts/part-001/DESIGN.md`

## Goal (as executed)

Add a `momentum_slope` sub-score (OLS slope over the 24-point `price_series`,
normalised to [-1,+1]) and re-balance the composite with OPTION A (gentle): the old
0.30 trend weight split into 0.20 trend + 0.10 momentum_slope.

## Recovery / scope change (recorded)

BLOCKER found mid-slice: `DataBook` did NOT carry `price_series` — it was dropped at
`build_databook` and never reached L2, so momentum could not be computed. User
green-lit OPTION A: widen the L1 DataBook contract to carry `price_series` (additive,
defaulted empty, folded into book_hash). The DESIGN's original "liquidity-trend +
discount-premium-series" stays out of scope (fixtures carry no volume series / only a
single-point discount_premium).

## What shipped

- `src/stackfund/contracts/databook.py`
  - added `price_series: tuple[float, ...]` (defaulted empty). Never crosses the
    firewall — L3 still only sees the bucketed ScenarioSeed.
- `src/stackfund/l1_databook/book.py`
  - `build_databook` takes + hashes `price_series`; `load_databook_from_fixture` and
    the live `load_databook` both carry the fixture series.
- `src/stackfund/l2_scorecard/scorecard.py`
  - `_momentum_slope` (OLS slope / mean price × 200, clipped [-1,+1]; 0.0 if <5 pts).
  - `build_scorecard` computes `momentum_slope_score`.
- `src/stackfund/contracts/scorecard.py`
  - added `momentum_slope_score` field (defaulted 0.0); composite is now
    `0.20*trend + 0.10*momentum_slope + 0.25*valuation + 0.20*fundamental
     + 0.15*catalyst - 0.10*risk`.
- `skills/etf-analysis/references/scoring-rules.md`: synced the sub-score table + formula.
- `tests/test_engine.py`: +3 tests (momentum from rising/falling/short series,
  Option-A composite, neutral momentum on no-series book).

## Demo-signature check (the point of Option A)

All 8 ETFs KEPT their action after the re-balance — only benefit_bps shifted modestly:
- 0056 REBALANCE +5.00pp (benefit 81 -> 92bps)
- 0050 / 006208 / 00850 NO_ACTION (cost gate; 00850 now 1.1bps short — closer)
- 00878 NO_ACTION (within tolerance)
- 00919 / 00713 / 00929 REBALANCE +5.00pp
No NO_ACTION<->REBALANCE flips. Gentle re-balance preserved the demo signature.

## Verification evidence

- `uv run pytest -q` -> 72 passed, 2 skipped (was 70; +3 momentum tests, existing
  decision/composite assertions still hold).
- `uv run lint-imports` -> Contracts: 3 kept, 0 broken (firewall intact after the
  L1 contract widening).
- `uv run ruff check` (5 changed files) -> All checks passed (fixed B905 zip strict=).
- `uv run python -m stackfund verify` -> determinism OK.
- `pipeline` and `pipeline --json` exit 0; scorecard determinism OK.

## Manual QA

- `pipeline`: momentum_slope contributes; decisions unchanged; ASCII-console-safe.
- momentum_slope positive for all 8 fixtures (all series rise over 24 days), which is
  correct given the fixture data.

## Firewall

- L1 DataBook widening does not touch L3/L4/L5 imports. L3 still reads only the
  bucketed ScenarioSeed (NOT price_series). `lint-imports` 3 kept / 0 broken.

## Incident links

None (blocker resolved in-slice via the user-approved scope widening).
