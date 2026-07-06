# part-001 TODO

Design authority: `.beacon/parts/part-001/DESIGN.md`

## SLICE Map

### part-001-slice-001: Crowd voices + reaction chain + etf rank/distance + SKILL rewrite

Status: done (archived at `.beacon/done/part-001/`)

Goal: Kill the "single-note" crowd feel and surface etf worth-acting; slim both SKILL.md.

Outcome: 10 archetypes speak distinctly; a herding-ordered reaction chain is emitted;
pipeline prints a worth-acting ranking and a NO_ACTION distance-to-threshold.

Candidate scope:
- [x] engine.py `_ARCHETYPE_VOICE` (per-stance line per archetype)
- [x] engine.py `_HERDING` + `_reaction_chain` (who-moves-first storyline)
- [x] cli.py `_print_action_ranking` (net edge = benefit - cost)
- [x] cli.py NO_ACTION `gap_to_threshold_bps` display
- [x] both SKILL.md rewritten as operation manuals
- [x] fixed U+2212 cp950 console crash

Verification target:
- Unit: `uv run pytest -q`
- Regression: `uv run lint-imports`, `uv run ruff check`
- Manual QA: `python -m stackfund crowd`, `python -m stackfund pipeline`

Done gate:
- 60 passed / 2 skipped; 3 kept / 0 broken; determinism OK; output ASCII-safe. MET.

### part-001-slice-002: Per-archetype stance from ordinal-context sensitivity

Status: done (archived at `.beacon/done/part-001/part-001-slice-002-done-current.md`)

Goal: Replace the single global stance flip with each archetype reacting to the frozen
ordinal context by its own sensitivity — still deterministic, still scalar-free.

Outcome: In the same scenario, archetypes no longer all flip together; e.g. a
yield_seeker leans pro only when yield bucket is favourable, a leveraged player is
sensitive to extreme buckets — driven by `ScenarioSeed.ordinal_context`.

Candidate scope:
- [ ] engine.py: per-archetype sensitivity map keyed by ordinal bucket
- [ ] engine.py: `_stance_for` reads ordinal context (not just global consensus)
- [ ] keep `crowd_consensus` derivation deterministic from seed
- [ ] add tests covering PersonaReaction stance variation across buckets
- [ ] update personas.md if the stance model description changes

Forbidden scope:
- No numeric scalar on CrowdNarrative / PersonaReaction (schema enum stays -1|0|1)
- No L3 import of L1/L2/L4/L5
- No change to etf-analysis or the deterministic trunk

Verification target:
- Unit: `uv run pytest -q` (add stance-variation test)
- Regression: `uv run lint-imports`, `uv run ruff check src/stackfund/l3_crowd/engine.py`
- Manual QA: `python -m stackfund crowd` under 2+ scenarios; `verify` determinism

Done gate:
- pytest green, 3 kept / 0 broken, determinism OK; stance visibly varies by archetype.

### part-001-slice-003: Scenario horizon/intensity dimensions

Status: done (archived at `.beacon/done/part-001/part-001-slice-003-done-current.md`)

Goal: Add `--horizon {intraday,swing,long}` and `--intensity {mild,severe}` so the
same event yields different reaction chains at different time scales/strengths.

Candidate scope:
- [ ] ScenarioSeed: add horizon + intensity fields (feed seed_hash)
- [ ] make_seed + cmd_crowd: thread the new flags
- [ ] engine: chain emphasis shifts by horizon/intensity
- [ ] schema/scenario_seed update if committed schema exists
- [ ] tests: determinism with new dimensions

Forbidden scope:
- No firewall change; no numeric scalar; no trunk change

Verification target:
- Unit: `uv run pytest -q`
- Regression: `uv run lint-imports`
- Manual QA: `crowd --horizon intraday` vs `--horizon long` differ; `verify` OK

Done gate:
- Different horizon/intensity -> different chain; determinism preserved; gates green.

### part-001-slice-004: Scorecard new dimensions (highest risk)

Status: done (archived at `.beacon/done/part-001/part-001-slice-004-done-current.md`)
Note: scope resolved to `momentum_slope` (OLS over price_series) + Option-A gentle
composite re-balance; DataBook widened to carry price_series. Liquidity-trend /
discount-premium-series remain out of scope (fixtures lack the data).

Goal: Optionally add liquidity-trend + discount-premium-series sub-scores and
re-balance composite weights.

Candidate scope:
- [ ] l2_scorecard: new sub-scores from DataBook series
- [ ] contracts/scorecard: composite weight re-balance
- [ ] update scoring-rules.md + schema + scoring tests
- [ ] sanity-check demo numbers stay reasonable

Forbidden scope:
- No firewall change; keep NO_ACTION reason codes intact

Verification target:
- Unit: `uv run pytest -q` (update scoring + schema tests)
- Regression: `uv run lint-imports`, schema validation
- Manual QA: `pipeline` numbers reviewed for sanity

Done gate:
- All tests green; composite documented; demo numbers sane. (Consider separate PART.)
