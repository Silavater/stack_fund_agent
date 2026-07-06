# DONE snapshot — part-001-slice-002

Part: part-001
Slice: slice-002
Status: done
Date: 2026-07-06
Design authority: `.beacon/parts/part-001/DESIGN.md`

## Goal (as executed)

Replace the single global stance flip with per-archetype reactions to the frozen
ordinal context, so cohorts diverge within one scenario instead of moving in lockstep
— while keeping stance categorical (-1|0|1) and the narrative deterministic.

## What shipped

- `src/stackfund/l3_crowd/engine.py`
  - `_DISCOUNT_TILT` + `_YIELD_TILT`: ordinal buckets -> small ordinal tilt in [-1,+1].
  - `_ARCHETYPE_SENSITIVITY`: each archetype weights (discount_premium, yield) by its
    own character — value/yield cohorts read fundamentals; momentum/herd cohorts (0,0)
    ride the consensus only.
  - `_stance_for(archetype, consensus, ordinal)`: baseline consensus lean + the
    archetype's own weighted ordinal read (weight 0.9), thresholded back to -1|0|1.
  - `run_scenario` threads `seed.ordinal_context` into both stance + excerpt.
- `tests/test_crowd_engine.py` (new): 6 tests — categorical stance, 10 distinct
  voices, ordinal shifts stance at fixed consensus, momentum cohorts ignore
  fundamentals at fixed consensus, reaction chain present, full-narrative determinism.

## Design decision recorded

`make_seed` already folds ordinal context into `seed_hash`, so `crowd_consensus`
itself varies by fundamentals. slice-002 is specifically about the *per-archetype*
stance no longer being a lockstep flip of that one consensus. Tests isolate the
mechanism by calling `_stance_for` with a FIXED consensus and varying ordinal (an
earlier test drafted the wrong assumption — two ETFs also differ in consensus — and
was corrected).

## Verification evidence

- `uv run pytest -q` -> 66 passed, 2 skipped (was 60; +6 new crowd tests).
- `uv run lint-imports` -> Contracts: 3 kept, 0 broken.
- `uv run ruff check` (engine.py, test_crowd_engine.py) -> All checks passed.
- `uv run python -m stackfund verify --symbol 0056 --scenario 0056_cut`
  -> determinism: crowd_consensus 'bullish' == 'bullish' -> OK.

## Manual QA

- `crowd --symbol 00878 --scenario 升息` exit 0; ASCII-console-safe.
- Spread check: 0056 (discount/high) vs 00878 (rich/low) show different stance
  distributions; value cohorts pulled to neutral under rich+low-yield context.

## Firewall

- No numeric scalar added (stance stays enum -1|0|1). L3 imports no engine module.
  `lint-imports` 3 kept / 0 broken confirms L4/L5 still do not import FACE.

## Incident links

None.
