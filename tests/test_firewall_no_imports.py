"""Firewall guard (ast import-graph). Fast, zero-dependency belt-and-suspenders
alongside the declarative import-linter contracts in pyproject.toml.

Encodes the Core-B invariant: the L4 portfolio manager (and the L5 spend path)
must NEVER import the L3 crowd side-rail or any FACE artifact (CrowdNarrative /
NarrativeDivergence) — not "zero it out and re-run", but "structurally never
wired in".
"""

from __future__ import annotations

import ast
import pathlib

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "stackfund"

# package -> tokens it must never import
GUARDED = {
    "l4_portfolio": (
        "l3_crowd",
        "crowd_narrative",
        "narrative_divergence",
        "CrowdNarrative",
        "NarrativeDivergence",
    ),
    "l5_finops": (
        "l3_crowd",
        "crowd_narrative",
        "narrative_divergence",
        "CrowdNarrative",
        "NarrativeDivergence",
    ),
}


def _imported_names(path: pathlib.Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            yield module, node.lineno
            for alias in node.names:  # catch `from x import NarrativeDivergence`
                yield f"{module}.{alias.name}", node.lineno


def _cases():
    cases = []
    for pkg, forbidden in GUARDED.items():
        for py in sorted((SRC / pkg).rglob("*.py")):
            cases.append((py, forbidden))
    return cases


_CASES = _cases()


@pytest.mark.parametrize(
    "py,forbidden",
    _CASES,
    ids=[str(c[0].relative_to(SRC)) for c in _CASES],
)
def test_layer_does_not_import_crowd_side_rail(py, forbidden):
    violations = [
        f"{py}:{line} imports forbidden '{name}'"
        for name, line in _imported_names(py)
        for bad in forbidden
        if bad.lower() in name.lower()
    ]
    assert not violations, "FIREWALL BREACH (decision path must not touch L3/FACE):\n" + "\n".join(
        violations
    )


def test_cases_are_non_empty():
    assert _CASES, "expected L4/L5 python files to scan"
