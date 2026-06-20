# Output schema

The Pro report validates against `schemas/crowd_scenario_report.schema.json`
(Draft 2020-12):

- root `is_authoritative` is `const: false`;
- every object is `additionalProperties: false`;
- **no** price/NAV/discount/yield/weight/cap field exists anywhere in the schema;
- the only decision-shaped scalar is `contrarian_modifier.value ∈ [-1,+1]` (also
  `is_authoritative: false`, with a pinned `formula_id`);
- `disclaimer` is required (`minLength` 40), fail-closed.

The raw `ContrarianSignal` validates against
`schemas/contrarian_signal.schema.json`. A baked replay sample lives at
`fixtures/scenario_0056_cut.json` and is checked against the schema in
`tests/test_schema_validation.py`.
