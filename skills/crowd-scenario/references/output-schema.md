# Output schema

The Pro report validates against `schemas/crowd_scenario_report.schema.json`
(Draft 2020-12):

- the crowd artifact is `non_authoritative: const true`;
- every object is `additionalProperties: false`;
- **no** price/NAV/discount/yield/weight/cap field exists anywhere in the schema;
- there is **no decision-shaped numeric scalar** — the crowd stance is the
  categorical `crowd_consensus ∈ {bearish, neutral, bullish}` only;
- `disclaimer` is required (`minLength` 40), fail-closed.

The raw `CrowdNarrative` validates against
`schemas/crowd_narrative.schema.json`. A baked replay sample lives at
`fixtures/scenario_0056_cut.json` and is checked against the schema in
`tests/test_schema_validation.py`.
