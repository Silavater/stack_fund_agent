# part-001 Verification Report

PART: part-001 — StackFund skill enrichment (crowd + etf-analysis)
Status: done
Date: 2026-07-06
Design authority: `.beacon/parts/part-001/DESIGN.md`

## Slices delivered

| slice | outcome | archive |
| --- | --- | --- |
| slice-001 | crowd per-archetype voices + reaction chain; etf worth-acting ranking + NO_ACTION distance; both SKILL.md rewritten; cp950 crash fixed | `part-001-slice-001-done-current.md` |
| slice-002 | per-archetype stance from ordinal-context sensitivity (no lockstep flip) | `part-001-slice-002-done-current.md` |
| slice-003 | scenario `--horizon` / `--intensity` dimensions feeding seed_hash | `part-001-slice-003-done-current.md` |
| slice-004 | `momentum_slope` scorecard sub-score + Option-A composite re-balance; DataBook widened to carry price_series | `part-001-slice-004-done-current.md` |

## Final gate (whole PART)

- `uv run pytest -q` -> 72 passed, 2 skipped (baseline was 60; +12 net new tests).
- `uv run lint-imports` -> Contracts: 3 kept, 0 broken (firewall intact throughout).
- `uv run ruff check` on all changed files -> All checks passed.
- `uv run python -m stackfund verify` -> crowd determinism OK.
- scorecard determinism OK; `pipeline` + `pipeline --json` exit 0.

## Firewall integrity

Preserved end-to-end. The crowd FACE stayed scalar-free (stance enum -1|0|1); L3
never imports L1/L2/L4/L5; L4/L5 never import any FACE artifact. slice-004's L1
DataBook widening (price_series) does not reach L3 — the crowd still reads only the
bucketed ScenarioSeed.

## Demo signature

All 8 ETF decisions kept their action after the slice-004 composite re-balance
(0056 REBALANCE +5, 0050/006208/00850/00878 NO_ACTION, 00919/00713/00929 REBALANCE +5)
— only benefit_bps shifted modestly. Option-A gentle weighting achieved its goal.

## Known deferrals (backlog for a future PART)

- Liquidity-trend + discount-premium-series sub-scores — need a fixture-schema change
  to carry a volume series; deliberately out of scope.
- Live LLM persona text layer — a documented seam, not wired.

## Manual QA performed

- `python -m stackfund crowd` across scenarios + horizons: distinct voices, horizon
  shifts the chain lead, ASCII-console-safe.
- `python -m stackfund pipeline`: ranking + NO_ACTION distance render; decisions sane.
