# Beacon Plan

## Project Goal

Upgrade StackFund's two Agent Skills — `crowd-scenario` and `etf-analysis` — from
demo-grade to a durable long-term product. Primary pain: the crowd engine is
single-note (identical canned persona text, global stance flip, no real reaction
chain). Secondary: etf-analysis is solid but can be broadened. All changes must
preserve the machine-enforced firewall (L3 non-authoritative, no numeric scalar,
L4/L5 never import FACE).

## Non-goals

- Breaking or weakening the crowd firewall (no numeric scalar in CrowdNarrative;
  L4/L5 must never import L3/report).
- Placing any securities order (research/education only, always).
- Rewriting the deterministic engine trunk beyond the scoped scorecard extension.
- Wiring a live LLM persona layer (stays a documented seam).

## PARTs

| PART | Status | Goal | Design | TODO |
| --- | --- | --- | --- | --- |
| part-001 | done | Skill enrichment (crowd voices/chain/dimensions + etf rank/distance/scorecard) | `.beacon/parts/part-001/DESIGN.md` | `.beacon/parts/part-001/TODO.md` |

## Success Criteria

- Each of the 10 crowd archetypes speaks in its own voice; a real who-moves-first
  reaction chain is emitted. (DONE, slice-001)
- etf-analysis surfaces a worth-acting ranking and NO_ACTION distance-to-threshold.
  (DONE, slice-001)
- Per-archetype stance is driven by each archetype's own sensitivity to ordinal
  context, not a single global flip. (slice-002)
- Scenario gains horizon/intensity dimensions producing distinct reaction chains.
  (slice-003)
- Scorecard optionally gains new dimensions (liquidity trend, discount-premium
  series) with composite re-balanced and demo numbers sane. (slice-004, highest risk)
- Every slice: `pytest` green, `lint-imports` 3 kept / 0 broken, crowd determinism OK.

## Global Risks

- Changing consensus logic (slice-002) shifts existing journal/demo consensus values.
- Adding ScenarioSeed dimensions (slice-003) can break determinism if seed_hash
  does not incorporate the new fields.
- Extending the L2 scorecard (slice-004) rebalances composite → shifts every
  decision number and touches schema + scoring tests. Highest blast radius.

## Global Verification Strategy

Batched gates. After each slice: `uv run pytest -q`, `uv run lint-imports`,
`uv run ruff check` on changed files, and `uv run python -m stackfund verify`
for crowd determinism. A slice is not done until all four are green. Manual QA:
run `pipeline` and `crowd` and read the rendered output.
