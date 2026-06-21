# Firewall contract (executable rules)

The crowd layer (L3) is a **pure narrative side-rail**. Five enforced layers:

1. **Type** — `CrowdNarrative` has no price/nav/discount/yield/weight/cap field,
   and carries **no numeric scalar** — only a categorical `crowd_consensus`. By
   type it cannot return an authoritative number.
   (`src/stackfund/contracts/crowd_narrative.py`)
2. **Import** — L3 imports no L1/L2/L4/L5 compute module.
   (`import-linter` forbidden contracts + `tests/test_firewall_no_imports.py`)
3. **Input** — L3 reads only a frozen `ScenarioSeed` (bucketed ordinal context;
   personas never see raw numbers). No setters.
4. **Flag** — `non_authoritative` is hard-wired `true` (`__post_init__` assert +
   schema `const: true`).
5. **Wiring** — the L4 decision path does **not** import or receive any crowd
   artifact. CI asserts the L4 import graph contains no L3 / crowd narrative, and
   `build_rebalance_plan`'s signature accepts only an `AuthoritativeState`
   (never a crowd input). (`tests/test_l4_signature.py`)

> Even under prompt-injection, the worst L3 can do is produce a vivid but wrong
> *story* — it is not wired to any decision or calculation, so it causes **zero**
> damage to any computed number or any action.
