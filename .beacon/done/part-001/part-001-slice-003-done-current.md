# DONE snapshot — part-001-slice-003

Part: part-001
Slice: slice-003
Status: done
Date: 2026-07-06
Design authority: `.beacon/parts/part-001/DESIGN.md`

## Goal (as executed)

Add `--horizon {intraday,swing,long}` and `--intensity {mild,severe}` so the same
event yields different reaction chains at different time-scales / strengths, feeding
`seed_hash` so determinism holds and the firewall stays intact.

## What shipped

- `src/stackfund/contracts/scenario_seed.py`
  - `HORIZONS` / `INTENSITIES` vocabularies; `horizon` + `intensity` fields (defaulted
    swing/mild); `__post_init__` asserts them in-vocabulary (categorical, no scalar).
- `src/stackfund/l1_databook/seed.py`
  - `make_seed` takes `horizon` + `intensity` (defaulted), folds both into `seed_hash`.
- `schemas/scenario_seed.schema.json`
  - added `horizon` / `intensity` as enum fields (additionalProperties stays false).
- `src/stackfund/l3_crowd/engine.py`
  - `_HORIZON_LEAD` / `_HORIZON_FRAME`; `_reaction_chain(samples, seed)` re-orders the
    chain by horizon (intraday -> fastest herder leads; long -> slow fundamentals cohort
    leads) and widens the tail framing under severe intensity; narrative header names
    the time-scale + intensity.
- `src/stackfund/cli.py`
  - `cmd_crowd` threads the two flags; `--horizon` / `--intensity` argparse choices.
- `tests/test_crowd_engine.py` (+5 tests): horizon changes chain lead, intensity changes
  tail framing, horizon/intensity determinism, ScenarioSeed rejects bad vocab.

## Design decision recorded

Backward compatibility: `make_seed` has 6+ callers; new params default (swing/mild) so
existing callers are unchanged. Consensus can stay the same across horizons (it reads
the full seed_hash which now includes horizon) — the *chain ordering* is what horizon
changes, which is the slice goal. Callers that pin a specific horizon get a distinct
seed_hash (distinct chain), as intended.

## Verification evidence

- `uv run pytest -q` -> 70 passed, 2 skipped (was 66; +4 net new crowd tests).
- `uv run lint-imports` -> Contracts: 3 kept, 0 broken.
- `uv run ruff check` (5 changed files) -> All checks passed.
- `uv run python -m stackfund verify --symbol 0056 --scenario 0056_cut`
  -> determinism: crowd_consensus 'bullish' == 'bullish' -> OK.

## Manual QA

- `crowd --horizon intraday`: PTT/Dcard 風向 leads. `--horizon long`: 外資視角 leads.
  Both exit 0. `--horizon long --intensity severe` exit 0.
- `crowd --horizon weekly` (bad vocab) -> argparse exit 2 (rejected). ASCII-safe output.

## Firewall

- No numeric scalar added; horizon/intensity are categorical enums. L3 imports no
  engine module. `lint-imports` 3 kept / 0 broken confirms L4/L5 still isolated.

## Incident links

None.
