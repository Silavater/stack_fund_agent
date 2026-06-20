"""JSON Schema validation at the engine boundary (plan -> validate -> execute).

Schemas are loaded from the repo ``schemas/`` directory by default; override
with ``STACKFUND_SCHEMA_DIR`` (set in the container so it works regardless of
where the package is installed).
"""

from __future__ import annotations

import dataclasses
import json
import os
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def schema_dir() -> Path:
    override = os.environ.get("STACKFUND_SCHEMA_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "schemas"


@cache
def _validator(schema_name: str) -> Draft202012Validator:
    schema = json.loads((schema_dir() / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def as_jsonable(obj: Any) -> Any:
    """Normalise a dataclass (or nested structure) into JSON-native types.

    ``dataclasses.asdict`` preserves tuples, which jsonschema does not treat as
    ``array``; round-tripping through JSON converts tuples to lists.
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        obj = dataclasses.asdict(obj)
    return json.loads(json.dumps(obj, ensure_ascii=False))


def validate(instance: Any, schema_name: str) -> None:
    """Raise ``jsonschema.ValidationError`` if ``instance`` is invalid."""
    _validator(schema_name).validate(instance)


def is_valid(instance: Any, schema_name: str) -> bool:
    return _validator(schema_name).is_valid(instance)
