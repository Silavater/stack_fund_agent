# DONE snapshot — part-001-slice-001

Part: part-001
Slice: slice-001
Status: done
Design authority: `.beacon/parts/part-001/DESIGN.md`

## Goal (as executed)

Kill the "single-note" crowd feel and surface etf worth-acting; slim both SKILL.md
into operation manuals.

## What shipped

- `src/stackfund/l3_crowd/engine.py`
  - `_ARCHETYPE_VOICE`: each of the 10 archetypes has its own per-stance line.
  - `_HERDING` + `_reaction_chain`: a herding-ordered who-moves-first storyline.
  - `_excerpt_for` / `_ZH_NAME` helpers; `run_scenario` now emits the chain.
- `src/stackfund/cli.py`
  - `_worth_acting_bps` + `_print_action_ranking`: net-edge (benefit - cost) ranking.
  - NO_ACTION cost-gate rows now carry `gap_to_threshold_bps` and print
    "X bps short of the Y bps cost threshold".
  - Imports `EXPECTED_BENEFIT_BELOW_TRANSACTION_COST` + `ALPHA_BPS`.
- `skills/crowd-scenario/SKILL.md` and `skills/etf-analysis/SKILL.md` rewritten:
  description trimmed to ~3 sentences, Quick start first, firewall prose demoted.

## Bug fixed during the slice

U+2212 (Unicode minus) in printed strings crashed the pipeline on Windows cp950
console (`UnicodeEncodeError`). Replaced all printed U+2212 / arrow / em-dash with
ASCII (`-`, `->`). Verified `pipeline` and `pipeline --json` exit 0.

## Verification evidence

- `uv run pytest -q` -> 60 passed, 2 skipped (matches baseline; zero regression).
- `uv run lint-imports` -> Contracts: 3 kept, 0 broken.
- `uv run ruff check` (cli.py, engine.py) -> All checks passed.
- `uv run ruff format --check` -> 2 files already formatted.
- `uv run python -m stackfund verify --symbol 0056 --scenario 0056_cut`
  -> determinism: crowd_consensus 'bullish' == 'bullish' -> OK.

## Manual QA

- `python -m stackfund crowd` across 0056_cut / 升息 / 電子權值回檔: distinct
  per-archetype voices + a 3-step reaction chain; determinism OK.
- `python -m stackfund pipeline`: ranking block + NO_ACTION distance render, ASCII-safe.

## Incident links

None.
