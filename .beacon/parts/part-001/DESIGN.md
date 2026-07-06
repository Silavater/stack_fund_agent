# part-001 DESIGN

## Goal

Enrich both StackFund skills so they stop being demo-thin: crowd personas gain
individual voices, per-archetype stance logic, added scenario dimensions, and a
real reaction chain; etf-analysis gains a worth-acting ranking, NO_ACTION
distance-to-threshold, and (optionally) new scorecard dimensions.

## Non-goals

- No firewall weakening: CrowdNarrative stays scalar-free; L4/L5 never import FACE.
- No securities orders. No live LLM persona wiring.

## Assumptions

- L3 reads only a frozen `ScenarioSeed` (bucketed ordinal context) and emits only a
  `CrowdNarrative` (categorical stance, no numeric scalar).
- `stance in {-1, 0, 1}` is fixed by schema enum — richer emotion cannot be encoded
  as a finer scalar; it lives in the excerpt text and the chain ordering.
- The deterministic trunk flows L4 -> L2 -> L1; report-time divergence is computed
  by the composer, never written back.
- Determinism is derived from `seed_hash`; any new seed input must feed the hash.

## Design Options

- Crowd voice: (a) static per-archetype template keyed by stance [chosen — simple,
  deterministic, firewall-safe] vs (b) live LLM text [deferred seam].
- Stance logic: (a) global flip by consensus [current] vs (b) per-archetype
  sensitivity to ordinal context [chosen for slice-002].
- Scorecard extension: (a) leave 5 sub-scores [current] vs (b) add liquidity trend +
  discount-premium series and re-balance composite weights [slice-004, highest risk].

## Chosen Design

Ship as four ordered slices, low-risk first, each behind its own gate:
- slice-001 (DONE): per-archetype voice + reaction chain (engine.py); etf rank +
  NO_ACTION distance (cli.py); both SKILL.md rewritten as operation manuals.
- slice-002: per-archetype stance driven by ordinal-context sensitivity.
- slice-003: `--horizon` / `--intensity` scenario dimensions feeding seed_hash.
- slice-004: optional scorecard dimensions with composite re-balance (highest risk).

## Verification Targets

- `uv run pytest -q` green (baseline 60 passed / 2 skipped).
- `uv run lint-imports` -> 3 kept, 0 broken.
- `uv run ruff check` clean on changed files.
- `uv run python -m stackfund verify --symbol 0056 --scenario 0056_cut` -> determinism OK.

## Unit Test Strategy

Add tests for previously-uncovered `PersonaReaction` / `ScenarioSeed` behaviour as
each slice touches them. slice-004 must update scoring + schema tests.

## Manual QA Strategy

Run `python -m stackfund crowd` (inspect distinct voices + chain) and
`python -m stackfund pipeline` (inspect ranking + distance). All printed output
must be ASCII-console-safe (cp950): no U+2212 / em-dash / arrow in printed strings.

## Risks

- slice-002 shifts existing consensus values (journal/demo); acceptable, note it.
- slice-003 determinism break if seed_hash omits new dimensions.
- slice-004 rebalances composite -> every decision number shifts; largest blast radius.

## Open Questions

- slice-004: keep it in scope, or move to a separate PART once 002/003 land?
