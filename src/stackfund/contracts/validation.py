"""Output-contract validation — the deterministic engine's serialization boundary.

The engine's structured outputs (the pipeline research report, the rebalance plan,
the crowd narrative) are validated against the committed JSON Schemas in
``schemas/`` *before* they are printed, so a malformed or contract-violating
artifact fails closed rather than reaching a consumer (a skill, the UI, a
downstream model).

``jsonschema`` is imported lazily — only this boundary needs it; the deterministic
core never imports it. The schema files ship as package data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


class ContractError(Exception):
    """A genuine output-contract violation — callers should fail closed."""


def _load(schema_name: str) -> dict:
    return json.loads((_SCHEMA_DIR / f"{schema_name}.schema.json").read_text(encoding="utf-8"))


def validate(obj: Any, schema_name: str) -> None:
    """Validate ``obj`` against ``schemas/<schema_name>.schema.json``.

    Raises :class:`ContractError` on a genuine violation. Lets
    ``ModuleNotFoundError`` (no ``jsonschema``) and ``FileNotFoundError`` (schema
    absent from the install) propagate, so the caller can decide whether to skip
    on an infrastructure gap or treat it as fatal.
    """
    import jsonschema  # lazy — only the contract boundary needs the dependency

    try:
        jsonschema.validate(obj, _load(schema_name))
    except jsonschema.ValidationError as exc:
        raise ContractError(f"{schema_name}: {exc.message}") from exc
