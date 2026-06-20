# Firewall contract (executable rules)

The crowd layer (L3) is a **pure narrative side-rail**. Five enforced layers:

1. **Type** — `ContrarianSignal` has no price/nav/discount/yield/weight/cap
   field. By type it cannot return an authoritative number.
   (`src/stackfund/contracts/contrarian_signal.py`)
2. **Import** — L3 imports no L1/L2/L4/L5 compute module.
   (`import-linter` forbidden contracts + `tests/test_firewall_no_imports.py`)
3. **Input** — L3 reads only a frozen `ScenarioSeed` (bucketed ordinal context;
   personas never see raw numbers). No setters.
4. **Flag** — `is_authoritative` is hard-wired `false` (`__post_init__` assert +
   schema `const: false`).
5. **Wiring** — the L4 decision path does **not** import or receive
   `ContrarianSignal`. CI asserts the L4 import graph contains no L3 / signal,
   and `build_rebalance_plan`'s signature accepts only `ScoreCard`.
   (`tests/test_l4_signature.py`)

> Even under prompt-injection, the worst L3 can do is produce a vivid but wrong
> *story* — it is not wired to any decision or calculation, so it causes **zero**
> damage to any computed number or any action.
