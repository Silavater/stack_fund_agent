# CURRENT

Status: planning-only

part-001 is complete — all four slices are done and archived under
`.beacon/done/part-001/`. No active executable SLICE is promoted.

## part-001 summary (done)

- slice-001: crowd per-archetype voices + reaction chain; etf worth-acting ranking +
  NO_ACTION distance-to-threshold; both SKILL.md rewritten; fixed a cp950 crash.
- slice-002: per-archetype stance from ordinal-context sensitivity (no more lockstep flip).
- slice-003: scenario `--horizon` / `--intensity` dimensions (horizon shifts who leads
  the reaction chain), fed into seed_hash.
- slice-004: `momentum_slope` scorecard sub-score over `price_series` + Option-A gentle
  composite re-balance; DataBook widened to carry the series. All 8 demo decisions held.

Final gate: `pytest` 72 passed / 2 skipped · `lint-imports` 3 kept / 0 broken ·
crowd + scorecard determinism OK · `pipeline` exit 0.

## Next

Backlog candidates for a future PART (not yet promoted):
- Liquidity-trend + discount-premium-series sub-scores (needs a fixture-schema change
  to carry a volume series — deliberately deferred).
- Live LLM persona text layer for the crowd narrative (documented seam).
