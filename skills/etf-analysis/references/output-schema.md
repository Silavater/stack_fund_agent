# Output schemas

This skill's outputs are validated against the repo's JSON Schemas:

- `schemas/etf_research_report.schema.json` — DataBook + ScoreCard bundle
  (mandatory `disclaimer`, fail-closed).
- `schemas/rebalance_plan.schema.json` — hard-only plan; `action` ∈
  {`NO_ACTION`, `REBALANCE`}; no crowd/modifier field exists in the schema.

Validate in code with:
```python
from stackfund.validation import validate, as_jsonable
validate(as_jsonable(plan), "rebalance_plan.schema.json")
```
